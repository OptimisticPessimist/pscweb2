import json
from copy import copy
from operator import attrgetter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rehearsal.models import Rehearsal, Actor, Attendance, Character, Scene, Appearance
from production.view_func import *


class AtndGraph(LoginRequiredMixin, TemplateView):
    '''出欠グラフのビュー
    '''
    template_name = 'rehearsal/attendance_graph.html'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けたハンドラ
        '''
        # URLconf から、Rehearsal を取得し、属性として持っておく
        rehearsals = Rehearsal.objects.filter(pk=self.kwargs['rhsl_id'])
        if len(rehearsals) < 1:
            raise Http404
        self.rehearsal = rehearsals[0]
        
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, self.rehearsal.production.id)
        if not prod_user:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # 戻るボタン用に、prod_id を渡す
        prod_id = self.rehearsal.production.id
        context['prod_id'] = prod_id
        
        # 役者リスト
        actr_list = list(
            Actor.objects.filter(production__pk=prod_id).order_by('name'))
        context['actrs'] = json.dumps([
            {'id': actr.id, 'name': actr.name, 'short_name': actr.short_name}
            for actr in actr_list
        ])
        
        # 登場人物リスト
        chr_list = list(
            Character.objects.filter(production__pk=prod_id))
        # chr_list の各要素に、対応する役者のインデックスを持つ
        for chr in chr_list:
            # 配役が actr_list の何番目かを取得
            if chr.cast in actr_list:
                chr.actr_idx = actr_list.index(chr.cast)
            else:
                # 配役がなければ -1
                chr.actr_idx = -1
        
        context['chrs'] = json.dumps([
            {'id': chr.id, 'name': chr.name, 'short_name': chr.short_name,
                'actr_idx': chr.actr_idx}
            for chr in chr_list
        ])
        
        # この稽古の、全役者の in/out 時刻のリスト
        time_borders = []
        for actr_idx, actr in enumerate(actr_list):
            atnds = actr.attendance_set.filter(rehearsal=self.rehearsal)
            for atnd in atnds:
                # 欠席なら除外
                if atnd.is_absent:
                    continue
                # in 時刻 - 稽古の開始時刻～終了時刻に収まるよう補正する
                from_time = self.rehearsal.start_time if atnd.is_allday\
                    else min(max(atnd.from_time, self.rehearsal.start_time),
                        self.rehearsal.end_time)
                time_borders.append({
                    'time': from_time.strftime('%H:%M'),
                    'actr_idx': actr_idx,
                    'move': 'in'
                })
                # out 時刻 - 稽古の開始時刻～終了時刻に収まるよう補正する
                to_time = self.rehearsal.end_time if atnd.is_allday\
                    else min(max(atnd.to_time, self.rehearsal.start_time),
                        self.rehearsal.end_time)
                time_borders.append({
                    'time': to_time.strftime('%H:%M'),
                    'actr_idx': actr_idx,
                    'move': 'out'
                })
        
        # シーンのリスト
        scenes = Scene.objects.filter(production__pk=prod_id)
        
        # シーンごとの時間スロット
        scns_time_slots = []
        for scene in scenes:
            # このシーンの出番のリスト
            scn_apprs = [appr for appr in scene.appearance_set.all()]
            # 元の chr_list から id だけ取り出したもの
            chr_ids = [chr.id for chr in chr_list]
            
            # scn_chrs に対応する chr_list のインデックスリストを作る
            chr_idxs = []
            for scn_appr in scn_apprs:
                # chr_list の何番目かを取得
                if scn_appr.character.id in chr_ids:
                    chr_idxs.append(chr_ids.index(scn_appr.character.id))
                else:
                    # 配役がなければ -1
                    chr_idxs.append(-1)
            
            # scene に情報として登場人物のインデックスのリストを追加
            scene.chr_idxs = chr_idxs
            # scene に情報として chr_idxs に対応するセリフ数のリストを追加
            scene.lines_nums = [
                Appearance.average_lines_num(scn_apprs)
                    if appr.lines_auto else appr.lines_num
                for appr in scn_apprs
            ]
            
            # scn_chrs に対応する役者のインデックスリストを作る
            actr_idxs = []
            for scn_appr in scn_apprs:
                # 配役が actr_list の何番目かを取得
                if scn_appr.character.cast in actr_list:
                    actr_idx = actr_list.index(scn_appr.character.cast)
                else:
                    # 配役がなければ -1
                    actr_idx = -1
                actr_idxs.append(actr_idx)
            
            # このシーンに出ている役者の時間スロットの境界のリスト
            scn_time_borders = [
                border for border in time_borders
                if border['actr_idx'] in actr_idxs]
            
            # scn_time_borders から、このシーンの時間スロットを作る
            # time でソート (in -> out の順序は保たれる)
            scn_time_borders = sorted(scn_time_borders, key=lambda x:x['time'])
            
            time = self.rehearsal.start_time.strftime('%H:%M')
            slots = []
            attendee = set()
            for border in scn_time_borders:
                # 次の時間ならスロット追加
                if border['time'] > time:
                    slots.append({
                        'from_time': time,
                        'to_time': border['time'],
                        'attendee': list(attendee)
                    })
                    # 次のスロット開始
                    time = border['time']
                
                if border['move'] == 'in':
                    attendee.add(border['actr_idx'])
                if border['move'] == 'out':
                    attendee.discard(border['actr_idx'])
            
            # 稽古の終了時刻に達していなかったらスロット追加
            if self.rehearsal.end_time.strftime('%H:%M') > time:
                slots.append({
                    'from_time': time,
                    'to_time': self.rehearsal.end_time.strftime('%H:%M'),
                    'attendee': list(attendee)
                })
            
            scns_time_slots.append(slots)
        
        context['scns'] = json.dumps([
            {'id': scn.id, 'name': scn.name, 'chr_idxs':scn.chr_idxs,
                'lines_nums': scn.lines_nums}
            for scn in scenes
        ])
        context['scns_time_slots'] = json.dumps(scns_time_slots)
        
        return context
