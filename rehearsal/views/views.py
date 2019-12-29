from operator import attrgetter
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import Http404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from production.models import Production
from rehearsal.models import Rehearsal, Scene, Place, Facility, Character,\
    Actor, Appearance, ScnComment, Attendance, AtndChangeLog
from rehearsal.forms import RhslForm, ChrForm, ActrForm, ScnApprForm,\
    ChrApprForm, AtndForm
from .view_func import *


class ProdBaseListView(LoginRequiredMixin, ListView):
    '''アクセス権を検査する ListView の Base class
    '''
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self)
        if not prod_user:
            raise PermissionDenied
        
        # アクセス中の ProdUser を view の属性として持っておく
        # テンプレートで追加ボタンの有無を決めるため
        self.prod_user = prod_user
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # 戻るボタン, 追加ボタン用の prod_id をセット
        context['prod_id'] = self.kwargs['prod_id']
        
        return context


class ProdBaseCreateView(LoginRequiredMixin, CreateView):
    '''アクセス権を検査する CreateView の Base class
    '''
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self)
        
        # production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.production = prod_user.production
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self)
        
        # production を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.production = prod_user.production
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとするレコードの production をセット
        instance = form.save(commit=False)
        instance.production = self.production
        
        messages.success(self.request, str(instance) + " を追加しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)


class ProdBaseUpdateView(LoginRequiredMixin, UpdateView):
    '''アクセス権を検査する UpdateView の Base class
    '''
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.production = self.get_object().production
        
        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # production を view の属性として持っておく
        # フォームに渡してバリデーションで使うため
        self.production = self.get_object().production

        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self, self.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class ProdBaseDetailView(LoginRequiredMixin, DetailView):
    '''アクセス権を検査する DetailView の Base class
    '''
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得する
        prod_id = self.get_object().production.id
        prod_user = accessing_prod_user(self, prod_id=prod_id)
        if not prod_user:
            raise PermissionDenied
        
        # アクセス中の ProdUser を view の属性として持っておく
        # テンプレートで編集ボタンの有無を決めるため
        self.prod_user = prod_user
        
        return super().get(request, *args, **kwargs)


class ProdBaseDeleteView(LoginRequiredMixin, DeleteView):
    '''アクセス権を検査する DeleteView の Base class
    '''
    template_name_suffix = '_delete'

    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # 編集権を検査する
        test_edit_permission(self, self.get_object().production.id)
        
        return super().get(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result


class RhslTop(LoginRequiredMixin, TemplateView):
    '''Rehearsal のトップページ
    '''
    template_name = 'rehearsal/top.html'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けたハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self)
        if not prod_user:
            raise PermissionDenied
        
        # production を view の属性として持っておく
        self.production = prod_user.production
        
        return super().get(request, *args, **kwargs)


class RhslList(ProdBaseListView):
    '''Rehearsal のリストビュー

    Template 名: rehearsal_list (default)
    '''
    model = Rehearsal
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        return Rehearsal.objects.filter(production__pk=prod_id)


class RhslCreate(ProdBaseCreateView):
    '''Rehearsal の追加ビュー
    '''
    model = Rehearsal
    form_class = RhslForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:rhsl_list', kwargs={'prod_id': prod_id})
        return url


class RhslUpdate(ProdBaseUpdateView):
    '''Rehearsal の更新ビュー
    '''
    model = Rehearsal
    form_class = RhslForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:rhsl_list', kwargs={'prod_id': prod_id})
        return url


class RhslDetail(ProdBaseDetailView):
    '''Rehearsal の詳細ビュー
    '''
    model = Rehearsal


class RhslDelete(ProdBaseDeleteView):
    '''Rehearsal の削除ビュー
    '''
    model = Rehearsal
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:rhsl_list', kwargs={'prod_id': prod_id})
        return url


class RhslAbsence(ProdBaseDetailView):
    '''Rehearsal の欠席・未定の人を表示するビュー
    '''
    model = Rehearsal
    template_name_suffix = '_absence'
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # 欠席の人のリスト
        atnds = self.get_object().attendance_set.order_by('actor__name')
        abs_list = [atnd.actor for atnd in atnds if atnd.is_absent]
        
        context['abs_list'] = abs_list
        
        # 遅刻・早退の人のリスト
        actors = Actor.objects.filter(production=self.get_object().production)\
            .order_by('name')
        atnd_actrs = [atnd.actor for atnd in atnds]
        prt_atnds = []
        for actor in actors:
            # この稽古のこの役者の、全日でも欠席でもない参加時間
            actr_atnds = sorted(
                [atnd for atnd in atnds if atnd.actor == actor
                    and not atnd.is_allday and not atnd.is_absent],
                key=attrgetter('from_time')
            )
            # 参加時間があるなら追加
            if actr_atnds:
                actr_str = actor.name + " (" + ",".join(
                    [a.from_time.strftime('%H:%M') + "-" + a.to_time.strftime('%H:%M')
                        for a in actr_atnds]
                ) + ")"
                prt_atnds.append(actr_str)
        
        context['prt_atnds'] = prt_atnds
        
        # 未定の人のリスト
        und_list = [actor for actor in actors if actor not in atnd_actrs]
        
        context['und_list'] = und_list
        
        return context


class PlcList(ProdBaseListView):
    '''Place のリストビュー

    Template 名: place_list
    '''
    # 施設ごとにリストにするので、モデルは Facility
    model = Facility
    template_name = 'rehearsal/place_list.html'
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        return Facility.objects.filter(production__pk=prod_id)


class PlcCreate(LoginRequiredMixin, CreateView):
    '''Facility を指定して Place を追加するビュー
    
    Template 名: place_form (default)
    '''
    model = Place
    fields = ('room_name', 'note')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # facility, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.facility = self.get_facility_from_request()
        self.production = self.facility.production

        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # facility を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.facility = self.get_facility_from_request()
        
        # 編集権を検査する
        test_edit_permission(self, self.facility.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとするレコードの facility をセット
        instance = form.save(commit=False)
        instance.facility = self.facility
        
        messages.success(self.request, str(instance) + " を追加しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.facility.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)
    
    def get_facility_from_request(self):
        '''リクエストから facility を取得して返す
        
        facility がなければ 404 エラーを投げる
        '''
        facilities = Facility.objects.filter(pk=self.kwargs['fclt_id'])
        if len(facilities) < 1:
            raise Http404
        return facilities[0]


class PlcUpdate(LoginRequiredMixin, UpdateView):
    '''Place を更新する時のビュー
    
    Template 名: place_form (default)
    '''
    model = Place
    fields = ('room_name', 'note')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # facility, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.facility = self.get_object().facility
        self.production = self.facility.production

        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # facility を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.facility = self.get_object().facility
        
        # 編集権を検査する
        test_edit_permission(self, self.facility.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.facility.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url
    
    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class PlcDelete(LoginRequiredMixin, DeleteView):
    '''Place の削除ビュー
    
    Template 名: place_delete
    '''
    model = Place
    template_name_suffix = '_delete'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # facility, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.facility = self.get_object().facility
        self.production = self.facility.production

        # 編集権を検査してアクセス中の公演ユーザを取得する
        prod_user = test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # production を view の属性として持っておく
        # 遷移先を決めるのに使うため
        self.production = self.get_object().facility.production
        
        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result


class FcltCreate(ProdBaseCreateView):
    '''Facility の追加ビュー
    '''
    model = Facility
    fields = ('name', 'url', 'note')
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url


class FcltUpdate(ProdBaseUpdateView):
    '''Facility の更新ビュー
    '''
    model = Facility
    fields = ('name', 'url', 'note')
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url


class FcltDelete(ProdBaseDeleteView):
    '''Facility の削除ビュー
    '''
    model = Facility
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:plc_list', kwargs={'prod_id': prod_id})
        return url


class ScnList(ProdBaseListView):
    '''Scene のリストビュー

    Template 名: scene_list (default)
    '''
    model = Scene
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        scenes = Scene.objects.filter(production__pk=prod_id)
            
        # 出番リストを各シーンのプロパティとして追加
        for scene in scenes:
            apprs = scene.appearance_set.order_by('character__sortkey')
            scene.apprs = ', '.join(
                [str(appr.character) for appr in apprs])
        
        return scenes


class ScnCreate(ProdBaseCreateView):
    '''Scene の追加ビュー
    '''
    model = Scene
    fields = ('name', 'sortkey', 'description', 'length', 'length_auto',
        'progress', 'priority', 'note')
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:scn_list', kwargs={'prod_id': prod_id})
        return url


class ScnUpdate(ProdBaseUpdateView):
    '''Scene の更新ビュー
    '''
    model = Scene
    fields = ('name', 'sortkey', 'description', 'length', 'length_auto',
        'progress', 'priority', 'note')
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:scn_list', kwargs={'prod_id': prod_id})
        return url


class ScnDetail(ProdBaseDetailView):
    '''Scene の詳細ビュー
    '''
    model = Scene
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # このシーンの出番のリスト
        scene = self.get_object()
        apprs = Appearance.objects.filter(scene=scene)\
            .order_by('character__sortkey')
        context['apprs'] = apprs
        
        # このシーンのコメントのリスト (作成日の新しい順)
        cmts = ScnComment.objects.filter(scene=scene)\
            .order_by('-create_dt')
        context['cmts'] = cmts
        
        return context


class ScnDelete(ProdBaseDeleteView):
    '''Scene の削除ビュー
    '''
    model = Scene
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:scn_list', kwargs={'prod_id': prod_id})
        return url


class ChrList(ProdBaseListView):
    '''Character のリストビュー

    Template 名: character_list (default)
    '''
    model = Character
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        return Character.objects.filter(production__pk=prod_id)


class ChrCreate(ProdBaseCreateView):
    '''Character の追加ビュー
    '''
    model = Character
    form_class = ChrForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:chr_list', kwargs={'prod_id': prod_id})
        return url


class ChrUpdate(ProdBaseUpdateView):
    '''Character の更新ビュー
    '''
    model = Character
    form_class = ChrForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:chr_list', kwargs={'prod_id': prod_id})
        return url


class ChrDetail(ProdBaseDetailView):
    '''Character の詳細ビュー
    '''
    model = Character
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)

        # この登場人物の出番のリスト
        apprs = Appearance.objects.filter(character=self.get_object())\
            .order_by('scene__sortkey')
        context['apprs'] = apprs
        
        return context


class ChrDelete(ProdBaseDeleteView):
    '''Character の削除ビュー
    '''
    model = Character
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:chr_list', kwargs={'prod_id': prod_id})
        return url


class ActrList(ProdBaseListView):
    '''Actor のリストビュー

    Template 名: actor_list (default)
    '''
    model = Actor
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        return Actor.objects.filter(production__pk=prod_id)\
            .order_by('name')


class ActrCreate(ProdBaseCreateView):
    '''Actor の追加ビュー
    '''
    model = Actor
    form_class = ActrForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.production.id
        url = reverse_lazy('rehearsal:actr_list', kwargs={'prod_id': prod_id})
        return url


class ActrUpdate(ProdBaseUpdateView):
    '''Actor の更新ビュー
    '''
    model = Actor
    form_class = ActrForm
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので production を渡す
        kwargs['production'] = self.production
        
        return kwargs
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:actr_list', kwargs={'prod_id': prod_id})
        return url


class ActrDetail(ProdBaseDetailView):
    '''Actor の詳細ビュー
    '''
    model = Actor
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)

        # 稽古のコマのリスト
        prod_id = self.get_object().production.id
        rhsls = Rehearsal.objects.filter(
            production__pk=prod_id).order_by('date', 'start_time')
        
        # 各コマの (稽古情報とこの役者の参加時間のリスト) のリスト
        atnds = []
        for i, rhsl in enumerate(rhsls):
            atnd = {}
            atnd['rhsl'] = rhsl
            # 稽古のコマごとに、参加時間のリストを作る
            slots = Attendance.objects.filter(actor=self.get_object(),
                rehearsal=rhsl).order_by('from_time')
            atnd['slots'] = slots
            atnds.append(atnd)
        
        context['atnds'] = atnds
        
        return context


class ActrDelete(ProdBaseDeleteView):
    '''Actor の削除ビュー
    '''
    model = Actor
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('rehearsal:actr_list', kwargs={'prod_id': prod_id})
        return url


class ScnApprCreate(LoginRequiredMixin, CreateView):
    '''シーン詳細から Appearance を追加する時のビュー

    Template 名: appearance_form (default)
    '''
    model = Appearance
    form_class = ScnApprForm
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # scene と production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.scene = self.get_scene_from_request()
        self.production = self.scene.production
        
        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので scene, production を渡す
        kwargs['scene'] = self.scene
        kwargs['production'] = self.production
        
        return kwargs
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # scene を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.scene = self.get_scene_from_request()
        # production はフォームに渡すために持っておく
        self.production = self.scene.production
        
        # 編集権を検査する
        test_edit_permission(self, self.scene.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとする appearance の scene をセット
        new_appr = form.save(commit=False)
        new_appr.scene = self.scene
        
        messages.success(self.request, str(new_appr) + " を追加しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        scn_id = self.scene.id
        url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        return url
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)
    
    def get_scene_from_request(self):
        '''リクエストから scene を取得して返す
        
        scene がなければ 404 エラーを投げる
        '''
        scenes = Scene.objects.filter(pk=self.kwargs['scn_id'])
        if len(scenes) < 1:
            raise Http404
        return scenes[0]


class ChrApprCreate(LoginRequiredMixin, CreateView):
    '''登場人物詳細から Appearance を追加する時のビュー

    Template 名: appearance_form (default)
    '''
    model = Appearance
    form_class = ChrApprForm
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # character と production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.character = self.get_character_from_request()
        self.production = self.character.production
        
        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので character, production を渡す
        kwargs['character'] = self.character
        kwargs['production'] = self.production
        
        return kwargs
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # character を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.character = self.get_character_from_request()
        # production はフォームに渡すために持っておく
        self.production = self.character.production
        
        # 編集権を検査する
        test_edit_permission(self, self.character.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとする appearance の character をセット
        new_appr = form.save(commit=False)
        new_appr.character = self.character
        
        messages.success(self.request, str(new_appr) + " を追加しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        chr_id = self.character.id
        url = reverse_lazy('rehearsal:chr_detail', kwargs={'pk': chr_id})
        return url
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)
    
    def get_character_from_request(self):
        '''リクエストから character を取得して返す
        
        character がなければ 404 エラーを投げる
        '''
        characters = Character.objects.filter(pk=self.kwargs['chr_id'])
        if len(characters) < 1:
            raise Http404
        return characters[0]


class ApprUpdate(LoginRequiredMixin, UpdateView):
    '''Appearance を更新する時のビュー

    Template 名: appearance_form (default)
    '''
    model = Appearance
    fields = ('lines_num', 'lines_auto')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']
        
        # scene, character, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.scene = self.get_object().scene
        self.character = self.get_object().character
        self.production = self.scene.production
        
        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']
        
        # 編集権を検査する
        test_edit_permission(self, self.get_object().scene.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        if self.page_from == 'scn':
            scn_id = self.object.scene.id
            url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        elif self.page_from == 'chr':
            chr_id = self.object.character.id
            url = reverse_lazy('rehearsal:chr_detail', kwargs={'pk': chr_id})
        else:
            prod_id = self.object.scene.production.id
            url = reverse_lazy('rehearsal:rhsl_top', kwargs={'prod_id': prod_id})
        
        return url
    
    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class ApprDelete(LoginRequiredMixin, DeleteView):
    '''Appearance の削除ビュー
    '''
    model = Appearance
    template_name_suffix = '_delete'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']

        # production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.production = self.get_object().scene.production

        # 編集権を検査する
        test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']

        # 編集権を検査する
        test_edit_permission(self, self.get_object().scene.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        if self.page_from == 'scn':
            scn_id = self.object.scene.id
            url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        elif self.page_from == 'chr':
            chr_id = self.object.character.id
            url = reverse_lazy('rehearsal:chr_detail', kwargs={'pk': chr_id})
        else:
            prod_id = self.object.scene.production.id
            url = reverse_lazy('rehearsal:rhsl_top', kwargs={'prod_id': prod_id})
        
        return url
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result


class ScnCmtCreate(LoginRequiredMixin, CreateView):
    '''シーン詳細から ScnComment を追加する時のビュー

    Template 名: scn_comment_form (default)
    '''
    model = ScnComment
    fields = ('comment',)
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # scene と production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.scene = self.get_scene_from_request()
        self.production = self.scene.production
        
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        # 編集権は不要
        prod_user = accessing_prod_user(self, self.production.id)
        if not prod_user:
            raise PermissionDenied
        
        # アクセス中の ProdUser を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.prod_user = prod_user
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # scene を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.scene = self.get_scene_from_request()
        
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        # 編集権は不要
        prod_user = accessing_prod_user(self, self.scene.production.id)
        if not prod_user:
            raise PermissionDenied
        
        # prod_user を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.prod_user = prod_user
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとする ScnComment の scene, mod_prod_user をセット
        new_cmt = form.save(commit=False)
        new_cmt.scene = self.scene
        new_cmt.mod_prod_user = self.prod_user
        new_cmt.save()
        
        messages.success(self.request, str(new_cmt) + " を追加しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        scn_id = self.scene.id
        url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        return url
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)
    
    def get_scene_from_request(self):
        '''リクエストから scene を取得して返す
        
        scene がなければ 404 エラーを投げる
        '''
        scenes = Scene.objects.filter(pk=self.kwargs['scn_id'])
        if len(scenes) < 1:
            raise Http404
        
        return scenes[0]


class ScnCmtUpdate(LoginRequiredMixin, UpdateView):
    '''シーン詳細から ScnComment を更新する時のビュー

    Template 名: scn_comment_form (default)
    '''
    model = ScnComment
    fields = ('comment',)
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # コメントの編集権を検査してアクセス中の公演ユーザを取得する
        # テンプレートで固定要素として表示するため
        self.prod_user = self.test_cmt_permission()
        
        # scene と production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.scene = self.get_object().scene
        self.production = self.scene.production
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # コメントの編集権を検査してアクセス中の公演ユーザを取得する
        # 保存時にインスタンスにセットするため
        self.prod_user = self.test_cmt_permission()
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとする ScnComment の mod_prod_user をセット
        new_cmt = form.save(commit=False)
        new_cmt.mod_prod_user = self.prod_user
        new_cmt.save()
        
        messages.success(self.request, str(new_cmt) + " を更新しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        scn_id = self.object.scene.id
        url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        return url
    
    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)
    
    def test_cmt_permission(self):
        '''コメントの編集権を検査する
        '''
        scn_cmt = self.get_object()
        
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, scn_cmt.scene.production.id)
        if not prod_user:
            raise PermissionDenied
        
        # 所有権も編集権なく、記入者でもない場合はアクセス拒否
        if not(prod_user.is_owner or prod_user.is_editor
                or prod_user == scn_cmt.mod_prod_user):
            raise PermissionDenied
        
        return prod_user


class ScnCmtDelete(LoginRequiredMixin, DeleteView):
    '''ScnComment の削除ビュー
    '''
    model = ScnComment
    template_name_suffix = '_delete'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # コメントの編集権を検査してアクセス中の公演ユーザを取得する
        # テンプレートで固定要素として表示するため
        self.prod_user = self.test_cmt_permission()
        
        # scene と production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.scene = self.get_object().scene
        self.production = self.scene.production
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # コメントの編集権を検査する
        self.test_cmt_permission()
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        scn_id = self.object.scene.id
        url = reverse_lazy('rehearsal:scn_detail', kwargs={'pk': scn_id})
        return url
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result
    
    def test_cmt_permission(self):
        '''コメントの編集権を検査する
        '''
        scn_cmt = self.get_object()
        
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, scn_cmt.scene.production.id)
        if not prod_user:
            raise PermissionDenied
        
        # 所有権も編集権なく、記入者でもない場合はアクセス拒否
        if not(prod_user.is_owner or prod_user.is_editor
                or prod_user == scn_cmt.mod_prod_user):
            raise PermissionDenied
        
        return prod_user


class AtndCreate(LoginRequiredMixin, CreateView):
    '''役者詳細から Attendance を追加する時のビュー

    Template 名: attendance_form (default)
    '''
    model = Attendance
    form_class = AtndForm
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']

        # actor, rehearsal, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.actor = self.get_actor_from_request()
        self.rehearsal = self.get_rehearsal_from_request()
        self.production = self.actor.production
        
        # 役者の production と 稽古の production が違ったら 404
        if self.actor.production != self.rehearsal.production:
            raise Http404
        
        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので actor, rehearsal を渡す
        kwargs['actor'] = self.actor
        kwargs['rehearsal'] = self.rehearsal
        
        return kwargs
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']
        
        # actor, rehearsal を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.actor = self.get_actor_from_request()
        self.rehearsal = self.get_rehearsal_from_request()
        
        # 役者の production と 稽古の production が違ったら 404
        if self.actor.production != self.rehearsal.production:
            raise Http404
        
        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.actor.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 追加しようとする attendance の actor, rehearsal をセット
        new_atnd = form.save(commit=False)
        new_atnd.actor = self.actor
        new_atnd.rehearsal = self.rehearsal
        
        # 変更履歴を保存
        prod_user = accessing_prod_user(self, self.rehearsal.production.id)
        change_log = AtndChangeLog(production=self.rehearsal.production,
            old_value='', new_value=new_atnd,
            changed_by=prod_user.user, changed_by_id=prod_user.id)
        change_log.save()
        
        messages.success(self.request, str(new_atnd) + " を追加しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        if self.page_from == 'actr':
            actr_id = self.actor.id
            url = reverse_lazy('rehearsal:actr_detail', kwargs={'pk': actr_id})
        elif self.page_from == 'rhsl':
            rhsl_id = self.rehearsal.id
            url = reverse_lazy('rehearsal:rhsl_detail', kwargs={'pk': rhsl_id})
        else:
            prod_id = self.object.actor.production.id
            url = reverse_lazy('rehearsal:rhsl_top', kwargs={'prod_id': prod_id})
        
        return url
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "追加できませんでした。")
        return super().form_invalid(form)
    
    def get_actor_from_request(self):
        '''リクエストから actor を取得して返す
        
        actor がなければ 404 エラーを投げる
        '''
        actors = Actor.objects.filter(pk=self.kwargs['actr_id'])
        if len(actors) < 1:
            raise Http404
        return actors[0]
    
    def get_rehearsal_from_request(self):
        '''リクエストから rehearsal を取得して返す
        
        rehearsal がなければ 404 エラーを投げる
        '''
        rehearsals = Rehearsal.objects.filter(pk=self.kwargs['rhsl_id'])
        if len(rehearsals) < 1:
            raise Http404
        return rehearsals[0]


class AtndUpdate(LoginRequiredMixin, UpdateView):
    '''Attendance を更新する時のビュー

    Template 名: attendance_form (default)
    '''
    model = Attendance
    form_class = AtndForm
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']

        # actor, rehearsal, production を view の属性として持っておく
        # テンプレートで固定要素として表示するため
        self.actor = self.get_object().actor
        self.rehearsal = self.get_object().rehearsal
        self.production = self.actor.production
        
        # 役者の production と 稽古の productin が違ったら 404
        if self.actor.production != self.rehearsal.production:
            raise Http404
        
        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.production.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        '''フォームに渡す情報を改変する
        '''
        kwargs = super().get_form_kwargs()
        
        # フォーム側でバリデーションに使うので actor, rehearsal を渡す
        kwargs['actor'] = self.actor
        kwargs['rehearsal'] = self.rehearsal
        
        return kwargs
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']
        
        # actor, rehearsal を view の属性として持っておく
        # 保存時にインスタンスにセットするため
        self.actor = self.get_object().actor
        self.rehearsal = self.get_object().rehearsal
        
        # 役者の production と 稽古の production が違ったら 404
        if self.actor.production != self.rehearsal.production:
            raise Http404
        
        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.actor.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 変更履歴を保存
        prod_user = accessing_prod_user(self, self.rehearsal.production.id)
        change_log = AtndChangeLog(production=self.rehearsal.production,
            old_value=self.get_object(), new_value=form.instance,
            changed_by=prod_user.user, changed_by_id=prod_user.id)
        change_log.save()

        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)
    
    def get_success_url(self):
        '''更新に成功した時の遷移先を動的に与える
        '''
        if self.page_from == 'actr':
            actr_id = self.actor.id
            url = reverse_lazy('rehearsal:actr_detail', kwargs={'pk': actr_id})
        elif self.page_from == 'rhsl':
            rhsl_id = self.rehearsal.id
            url = reverse_lazy('rehearsal:rhsl_detail', kwargs={'pk': rhsl_id})
        else:
            prod_id = self.object.actor.production.id
            url = reverse_lazy('rehearsal:rhsl_top', kwargs={'prod_id': prod_id})
        
        return url
    
    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class AtndDelete(LoginRequiredMixin, DeleteView):
    '''Attendance を削除する時のビュー

    Template 名: attendance_delete
    '''
    model = Attendance
    template_name_suffix = '_delete'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']
        
        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.get_object().actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.get_object().actor.production.id)
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # page_from を view の属性として持っておく
        # テンプレートでリンクの URL を決めるため
        self.page_from = self.kwargs['from']

        # ログイン中のユーザの役者でなければ、編集権を検査する
        actor_user = self.get_object().actor.prod_user
        if not actor_user or actor_user.user != self.request.user:
            test_edit_permission(self, self.get_object().actor.production.id)
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        if self.page_from == 'actr':
            actr_id = self.object.actor.id
            url = reverse_lazy('rehearsal:actr_detail', kwargs={'pk': actr_id})
        elif self.page_from == 'rhsl':
            rhsl_id = self.object.rehearsal.id
            url = reverse_lazy('rehearsal:rhsl_detail', kwargs={'pk': rhsl_id})
        else:
            prod_id = self.object.actor.production.id
            url = reverse_lazy('rehearsal:rhsl_top', kwargs={'prod_id': prod_id})
        
        return url
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)

        # 変更履歴を保存
        prod_user = accessing_prod_user(self, self.object.rehearsal.production.id)
        change_log = AtndChangeLog(production=self.object.rehearsal.production,
            old_value=self.object, new_value='',
            changed_by=prod_user.user, changed_by_id=prod_user.id)
        change_log.save()

        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result


class AtndChangeList(ProdBaseListView):
    '''AtndChangeList のリストビュー

    Template 名: atndchangelog_list (default)
    '''
    model = AtndChangeLog
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        logs = AtndChangeLog.objects.filter(production__pk=prod_id)\
            .order_by('-create_dt')
        
        return logs
