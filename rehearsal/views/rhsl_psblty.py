import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from rehearsal.models import Rehearsal, Actor, Attendance, Character, Scene, Appearance
from rehearsal.model_func import *
from production.view_func import *


class RhslPossibility(LoginRequiredMixin, TemplateView):
    '''稽古可能性のビュー
    '''
    template_name = 'rehearsal/rehearsal_possibility.html'
    
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
        
        # 稽古リストを渡す
        rehearsals = Rehearsal.objects.filter(production__pk=prod_id)
        rhsl_list = [{
            'id': rhsl.id,
            'place': str(rhsl.place),
            'date': rhsl.date.strftime('%Y-%m-%d'),
            'start_time': rhsl.start_time.strftime('%H:%M'),
            'end_time': rhsl.end_time.strftime('%H:%M')
        } for rhsl in rehearsals]
        context['rhsls'] = json.dumps(rhsl_list)
        
        # シーンリストを渡す
        scenes = Scene.objects.filter(production__pk=prod_id)
        scn_list = [{
            'id': scn.id,
            'name': scn.name,
            'length': scn.length
        } for scn in scenes]
        context['scns'] = json.dumps(scn_list)
        
        # 役者
        actors = Actor.objects.filter(production__pk=prod_id)
        
        # 時間スロットを得る
        rhsls_scns_slots = []
        for rhsl in rehearsals:
            scns_slots = time_slots_for_rehearsal(rhsl, actors=actors, scenes=scenes)
            rhsls_scns_slots.append({
                'rehearsal': rhsl,
                'scns_slots': scns_slots
            })
        
        # トータルの稽古時間（未使用）
        # total_rhsl_time = 0
        # for rhsl in rehearsals:
        #     start_time = rhsl.start_time.hour * 60 + rhsl.start_time.minute
        #     end_time = rhsl.end_time.hour * 60 + rhsl.end_time.minute
        #     total_rhsl_time += end_time - start_time
        
        # 登場人物ベースの稽古可能性データ
        psblty_in_chrs = []
        # 稽古ごと
        for rhsl_slots in rhsls_scns_slots:
            rhsl = rhsl_slots['rehearsal']
            
            scn_psblty = []
            # シーンごと
            for slots in rhsl_slots['scns_slots']:
                
                # シーンの登場人物数 (= 出番データの数)
                chrs_num = Appearance.objects.filter(scene=slots['scene']).count()
                
                # シーンの長さ
                # TODO: length_auto に対応すること
                scn_len = slots['scene'].length
                
                psblty = 0
                # スロットごとの「可能性の指標」を加算していく
                for slot in slots['time_slots']:
                    # 時間
                    from_time = slot['from_time'].hour * 60 + slot['from_time'].minute
                    to_time = slot['to_time'].hour * 60 + slot['to_time'].minute
                    slot_time = to_time - from_time
                    # 出席者の役数の合計
                    atnd_chrs_lists = [atnd['appearances'] for atnd in slot['attendee']]
                    atnd_chrs_num = 0
                    for chrs_list in atnd_chrs_lists:
                        atnd_chrs_num += len(chrs_list)
                    
                    # 可能性の指標 = 時間 * 出席する役者の役の数 / シーンの登場人物数 / シーンの長さ
                    psblty += slot_time * atnd_chrs_num / chrs_num / scn_len
                    
                    # print('possibility: {} x {} / {} = {}'.format(
                    #     slot_time, atnd_chrs_num, chrs_num,
                    #     slot_time * atnd_chrs_num / chrs_num))
                
                scn_psblty.append(psblty)
            psblty_in_chrs.append(scn_psblty)
        context['psblty_in_chrs'] = json.dumps(psblty_in_chrs)
        
        # 役者ベースの稽古可能性データ
        psblty_in_actrs = []
        # 稽古ごと
        for rhsl_slots in rhsls_scns_slots:
            rhsl = rhsl_slots['rehearsal']
            
            scn_psblty = []
            # シーンごと
            for slots in rhsl_slots['scns_slots']:
                
                # シーンの役者数
                scn_apprs = Appearance.objects.filter(scene=slots['scene'])
                scn_actrs = [appr.character.cast for appr in scn_apprs]
                actrs_num = len(list(set(scn_actrs)))
                
                # シーンの長さ
                # TODO: length_auto に対応すること
                scn_len = slots['scene'].length
                
                psblty = 0
                # スロットごとの「可能性の指標」を加算していく
                for slot in slots['time_slots']:
                    # 時間
                    from_time = slot['from_time'].hour * 60 + slot['from_time'].minute
                    to_time = slot['to_time'].hour * 60 + slot['to_time'].minute
                    slot_time = to_time - from_time
                    
                    # 可能性の指標 = 時間 * 出席する役者の役の数 / シーンに出ている役者の数 / シーンの長さ
                    psblty += slot_time * len(slot['attendee']) / actrs_num / scn_len
                    
                    # print('possibility: {} x {} / {} = {}'.format(
                    #     slot_time, len(slot['attendee']), actrs_num,
                    #     slot_time * len(slot['attendee']) / actrs_num))
                
                scn_psblty.append(psblty)
            psblty_in_actrs.append(scn_psblty)
        context['psblty_in_actrs'] = json.dumps(psblty_in_actrs)
        
        # セリフ数ベースの稽古可能性データ
        psblty_in_lines = []
        # 稽古ごと
        for rhsl_slots in rhsls_scns_slots:
            rhsl = rhsl_slots['rehearsal']
            
            scn_psblty = []
            # シーンごと
            for slots in rhsl_slots['scns_slots']:
                
                # シーンのセリフ数
                scn_apprs = Appearance.objects.filter(scene=slots['scene'])
                average_lines_num = Appearance.average_lines_num(scn_apprs)
                scn_lines = [average_lines_num if appr.lines_auto
                                else appr.lines_num
                    for appr in scn_apprs]
                lines_num = sum(scn_lines)
                
                # シーンの長さ
                # TODO: length_auto に対応すること
                scn_len = slots['scene'].length
                
                psblty = 0
                # スロットごとの「可能性の指標」を加算していく
                for slot in slots['time_slots']:
                    # 時間
                    from_time = slot['from_time'].hour * 60 + slot['from_time'].minute
                    to_time = slot['to_time'].hour * 60 + slot['to_time'].minute
                    slot_time = to_time - from_time
                    # 出席者のセリフ数の合計
                    atnd_chrs_lists = [atnd['appearances'] for atnd in slot['attendee']]
                    atnd_lines_num = 0
                    for chrs_list in atnd_chrs_lists:
                        chr_lines_num = 0
                        for chr in chrs_list:
                            chr_lines_num += chr['lines_num']
                        atnd_lines_num += chr_lines_num
                    
                    # 可能性の指標 = 時間 * 出席する役者のセリフ数 / シーンのセリフ数 / シーンの長さ
                    psblty += slot_time * atnd_lines_num / lines_num / scn_len
                    
                    # print('possibility: {} x {} / {} = {}'.format(
                    #     slot_time, atnd_lines_num, lines_num,
                    #     slot_time * atnd_lines_num / lines_num))
                
                scn_psblty.append(psblty)
            psblty_in_lines.append(scn_psblty)
        context['psblty_in_lines'] = json.dumps(psblty_in_lines)
        
        return context
