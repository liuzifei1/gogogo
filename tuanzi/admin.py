# 对管理员用户admin的文件
from django.contrib import admin
from tuanzi import models
admin.site.register(models.UserInfo)
admin.site.register(models.Tag)
admin.site.register(models.Post)
admin.site.register(models.Post2Tag)
admin.site.register(models.PostUpDown)
admin.site.register(models.Comment)
admin.site.register(models.following)
admin.site.register(models.Applications)
