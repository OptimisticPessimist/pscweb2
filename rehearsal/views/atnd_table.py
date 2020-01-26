import json
from operator import attrgetter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from rehearsal.models import Rehearsal, Actor, Attendance, Character, Scene, Appearance
from production.view_func import *


class AtndTable(LoginRequiredMixin, TemplateView):
    '''出欠表のビュー
    '''
    template_name = 'rehearsal/attendance_table.html'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けたハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self)
        if not prod_user:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # 戻るボタン用に、prod_id を渡す
        prod_id = self.kwargs['prod_id']
        context['prod_id'] = prod_id
        
        # 稽古リスト
        rehearsals = Rehearsal.objects.filter(production__pk=prod_id)
        rhsl_list = [{
            'id': rhsl.id,
            'place': str(rhsl.place),
            'date': rhsl.date.strftime('%Y-%m-%d'),
            'start_time': rhsl.start_time.strftime('%H:%M'),
            'end_time': rhsl.end_time.strftime('%H:%M')
        } for rhsl in rehearsals]
        context['rhsls'] = json.dumps(rhsl_list)
        
        # 役者リスト
        actr_list = list(
            Actor.objects.filter(production__pk=prod_id).order_by('name'))

        actrs = [{
            'name': actr.name,
            'short_name': actr.get_short_name()
        } for actr in actr_list]
        
        context['actrs'] = json.dumps(actrs)
        
        # 役者ごとの出欠の、稽古リストに対応するリスト (3次元配列)
        attendances = Attendance.objects.filter(actor__production__pk=prod_id)
        actrs_rhsl_atnds = []
        for actor in actr_list:
            # その役者の出欠
            actor_atnds = [atnd for atnd in attendances if atnd.actor == actor]
            rhsl_attnds = []
            for rehearsal in rehearsals:
                # その稽古の出欠
                slots = sorted(
                    [atnd for atnd in actor_atnds if atnd.rehearsal == rehearsal],
                    key=attrgetter('from_time')
                )
                atnds = []
                for slot in slots:
                    atnds.append(
                        # 全日の場合
                        '*' if slot.is_allday
                        # 欠席の場合
                        else '-' if slot.is_absent
                        # さもなくば時間帯
                        else slot.from_time.strftime('%H:%M') + '-'
                            + slot.to_time.strftime('%H:%M')
                    )
                rhsl_attnds.append(atnds)
            actrs_rhsl_atnds.append(rhsl_attnds)
        
        context['actr_atnds'] = json.dumps(actrs_rhsl_atnds)
        
        # 登場人物のリスト
        characters = Character.objects.filter(production__pk=prod_id)
        chrs = []
        for character in characters:
            # 配役が actr_list の何番目かを取得
            if character.cast in actr_list:
                actr_idx = actr_list.index(character.cast)
            else:
                # 配役がなければ -1
                actr_idx = -1
            chrs.append({
                'name': character.name,
                'short_name': character.short_name,
                'cast_idx': actr_idx
            })
        
        context['chrs'] = json.dumps(chrs)
        
        # シーン名リスト
        scenes = Scene.objects.filter(production__pk=prod_id)
        context['scenes'] = json.dumps([scn.name for scn in scenes])

        # シーンごとの登場人物とセリフ数のリスト
        appearances = Appearance.objects.filter(scene__production__pk=prod_id)
        scenes_chr_apprs = []
        for scene in scenes:
            # シーン単品での出番のリスト
            scene_apprs = [appr for appr in appearances if appr.scene == scene]
            # 有効なセリフ数の平均値
            avrg_lines_mun = Appearance.average_lines_num(scene_apprs)
            # そのシーンに出ている人物のセリフ数のリスト
            chr_apprs = []
            for chr_idx, character in enumerate(characters):
                apprs = [appr for appr in scene_apprs if appr.character == character]
                if len(apprs) > 0:
                    # セリフ数 (自動なら平均値)
                    lines_num = avrg_lines_mun if apprs[0].lines_auto else apprs[0].lines_num
                    chr_apprs.append({
                        'chr_idx': chr_idx,
                        'lines_num': lines_num
                    })
            scenes_chr_apprs.append(chr_apprs)
        
        context['scenes_chr_apprs'] = json.dumps(scenes_chr_apprs)
        
        return context
