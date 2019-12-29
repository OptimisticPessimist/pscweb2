from django.conf import settings
from django.db import models
from production.models import Production, ProdUser


class Script(models.Model):
    '''台本
    '''
    title = models.CharField('題名', max_length=50)
    author = models.CharField('著者', max_length=50, blank=True)
    raw_data = models.TextField('データ', blank=True)
    FORMAT_CHOICES = (
        (1, 'Fountain JA'),
    )
    format = models.IntegerField('フォーマット', default=1,
        choices=FORMAT_CHOICES)
    create_dt = models.DateTimeField('作成日時', auto_now_add=True)
    modify_dt = models.DateTimeField('変更日時', auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name='所有者', on_delete=models.CASCADE)
    PUBLIC_LEVEL_CHOICES = (
        (1, '公開しない'),
        (2, 'PSCWEB2 ユーザ'),
    )
    public_level = models.IntegerField('公開レベル', default=1,
        choices=PUBLIC_LEVEL_CHOICES)
    
    class Meta:
        verbose_name = verbose_name_plural = '台本'
    
    def __str__(self):
        return self.title
