from django.core.exceptions import PermissionDenied
from .models import ProdUser


def accessing_prod_user(view, prod_id=None):
    '''アクセス情報から対応する ProdUser を取得する
    
    Parameters
    ----------
    view : View
        アクセス情報の取得元の View
    prod_id : int
        URLconf に prod_id が無い場合に指定する
    '''
    if not prod_id:
        prod_id=view.kwargs['prod_id']
    prod_users = ProdUser.objects.filter(
        production__pk=prod_id, user=view.request.user)
    if len(prod_users) < 1:
        return None
    return prod_users[0]


def test_edit_permission(view, prod_id=None):
    '''編集権を検査する
    
    Returns
    -------
    prod_user : ProdUser
        編集権を持っているアクセス中の ProdUser
    '''
    # アクセス情報から公演ユーザを取得する
    prod_user = accessing_prod_user(view, prod_id=prod_id)
    if not prod_user:
        raise PermissionDenied
    
    # 所有権または編集権を持っていなければアクセス拒否
    if not (prod_user.is_owner or prod_user.is_editor):
        raise PermissionDenied
    
    return prod_user


def test_owner_permission(view, prod_id=None):
    '''所有権を検査する
    
    Returns
    -------
    prod_user : ProdUser
        所有権を持っているアクセス中の ProdUser
    '''
    # アクセス情報から公演ユーザを取得する
    prod_user = accessing_prod_user(view, prod_id=prod_id)
    if not prod_user:
        raise PermissionDenied
    
    # 所有権または編集権を持っていなければアクセス拒否
    if not (prod_user.is_owner):
        raise PermissionDenied
    
    return prod_user
