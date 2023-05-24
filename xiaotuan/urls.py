# 这个文件对路由进行了定义，确保在对应的url路径可以执行对应的功能

from django.contrib import admin
from django.urls import path,re_path
from django.views.static import serve
from tuanzi import views
from xiaotuan import  settings
from django.urls import include
from django.conf.urls import url
from dailyreport import viewss

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login, name='login'),
    path('createp2t/', views.createp2t, name='createp2t'),
    path('logout/', views.logout),
    path('myidol/', views.myidol, name='myidol'),
    path('followta/<int:clubid>', views.followta, name='followta'),
    path('index/<int:x>/<int:pindex>', views.index, name='index'),
    path('get_validCode_img/', views.get_valid_code_img),
    path('register/', views.register),
    url(r'^myreport/$', viewss.MyReportView.as_view(), name='myreport'),
    url(r'^myreport/create$', viewss.ReportCreateView.as_view(), name='myreport-create'),
    url(r'^myreport/detail$', viewss.ReportDetailView.as_view(), name='myreport-detail'),
    path('clubinfo/<str:username>/',views.clubinfo),
    re_path(r"media(?P<path>.*)$",serve,{"document_root":settings.MEDIA_ROOT}),
    re_path('^(?P<username>\w+)/posts/(?P<post_id>\d+)$', views.post_detail),
    path('createpost/', views.createpost, name='createpost'),
    path("digg/",views.digg),
    path("comment/",views.comment),
    path("get_comment_tree/",views.get_comment_tree),
    path("cgpwd/", views.cgpwd, name='cgpwd'),
    path("modifya/", views.modifya, name='modifya'),
    path("createapplication/", views.createapplication, name='createapplication'),
    path("searchtag/", views.searchtag, name='searchtag'),
    path("hotrank/<int:pindex>",views.hotrank,name='hotrank'),
    path("upload/",views.upload),
    re_path('^$', views.login),
    path("interest/<int:pindex>",views.interest,name='interest')

]
