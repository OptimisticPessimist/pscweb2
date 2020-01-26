import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from rehearsal.models import Scene, Character, Actor, Appearance
from production.view_func import *


class ApprTable(LoginRequiredMixin, TemplateView):
    '''香盤表のビュー
    '''
    template_name = 'rehearsal/appearance_table.html'
    
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
        
        # シーン名リスト
        scenes = Scene.objects.filter(production__pk=prod_id)
        context['scenes'] = json.dumps([scn.name for scn in scenes])
        
        # 登場人物名リスト
        characters = Character.objects.filter(production__pk=prod_id)
        context['characters'] = json.dumps([chr.get_short_name() for chr in characters])
        
        # 役者名リスト
        actors = Actor.objects.filter(production__pk=prod_id)
        context['cast'] = json.dumps([actr.get_short_name() for actr in actors])
        
        # 各シーンの登場人物ごとの出番 (セリフ数) のリスト
        appearances = Appearance.objects.filter(scene__production__pk=prod_id)
        scenes_chr_apprs = []
        for scene in scenes:
            # シーン単品での出番のリスト
            scene_apprs = [appr for appr in appearances if appr.scene == scene]
            # 有効なセリフ数の平均値
            avrg_lines_num = Appearance.average_lines_num(scene_apprs)
            # そのシーンの、登場人物全員分のセリフ数のリスト
            chr_apprs = []
            for character in characters:
                apprs = [appr for appr in scene_apprs if appr.character == character]
                if len(apprs) > 0:
                    # セリフ数 (自動なら平均値)
                    chr_apprs.append(
                        avrg_lines_num if apprs[0].lines_auto else apprs[0].lines_num)
                else:
                    # 出番がないなら -1 を入れる
                    chr_apprs.append(-1)
            scenes_chr_apprs.append(chr_apprs)
        
        context['chr_apprs'] = json.dumps(scenes_chr_apprs)
        
        # 各シーンの役者の出番 (セリフ数) のリスト
        cast_for_chrs = []
        # まず、各登場人物の配役が actors の何番目にあるかのリストを作る
        for character in characters:
            if character.cast in actors:
                actr_idx = list(actors).index(character.cast)
            else:
                # 配役がなければ -1
                actr_idx = -1
            cast_for_chrs.append(actr_idx)
        
        scenes_cast_apprs = []
        # シーンごとに見ていく
        for chr_apprs in scenes_chr_apprs:
            actr_apprs = []
            # 役者ごとに演じる人物のセリフ数を足していく
            for actr_idx, actr in enumerate(actors):
                lines_num = 0
                appearing = False
                # 登場人物ごとにキャストのインデックスを見ていく
                for chr_idx, cast in enumerate(cast_for_chrs):
                    # インデックスが外側のループと等しければ、そのセリフ数を足す
                    if cast == actr_idx:
                        if chr_apprs[chr_idx] >= 0:
                            lines_num += chr_apprs[chr_idx]
                            appearing = True
                if appearing:
                    actr_apprs.append(lines_num)
                # その役者の出番がなかったら、-1 を入れる
                else:
                    actr_apprs.append(-1)
            scenes_cast_apprs.append(actr_apprs)
        
        context['cast_apprs'] = json.dumps(scenes_cast_apprs)
        
        return context
