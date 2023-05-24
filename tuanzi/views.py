# 本文件是用户的视图，也是本项目重要的核心文件之一
# 本文件实现了注册、登录、发帖等等后端核心功能
from datetime import datetime
from email.mime import application
import imp
import random
from urllib import response
from bs4 import BeautifulSoup
from django.shortcuts import render, HttpResponse, redirect
from django.contrib import auth
from django.urls import reverse
from tuanzi.Myforms import AvatarForm, UserForm, ChangePasswordForm
from tuanzi.models import Applications, Post, Post2Tag, Tag, UserInfo, following, User2Tag
from tuanzi.utils import validCode
from tuanzi import models
import json
from django.http import JsonResponse
from django.db.models import F, Count
from django.db.models.functions import TruncMonth
from django.db import transaction
from django.contrib.auth.decorators import login_required
import os
from xiaotuan import settings
from django.core.paginator import Paginator
import random
from datetime import datetime
from django.db.models import Q

# 登录视图函数
def login(request):
    #对用户名、密码以及验证码进行验证，均通过即登录成功
    if request.method == "POST":
        response = {"user": None, "msg": None}
        user = request.POST.get("user")
        pwd = request.POST.get("pwd")
        valid_code = request.POST.get("valid_code")
        valid_code_str = request.session.get("valid_code_str")
        if valid_code.upper() == valid_code_str.upper():
            user = auth.authenticate(username=user, password=pwd)
            if user:
                #request.user== 当前登录对象
                auth.login(request, user)  
                response["user"] = user.username
            else:
                response["msg"] = "用户名或者密码错误!"
        else:
            response["msg"] = "验证码错误!"
        return JsonResponse(response)
    return render(request, "login.html")


# 基于PIL模块动态生成响应状态码图片
def get_valid_code_img(request):
    img_data = validCode.get_valid_code_img(request)
    return HttpResponse(img_data)


# 注销视图，用于用户登出，之后可以重新登录或是换账号重新登录
def logout(request):
    auth.logout(request)  
    return redirect("/login/")


# 系统首页的视图
def index(request, x, pindex=1):
    mywhere = ""
    #搜索功能，keyword为搜索词
    search = request.GET.get("keyword", None)
    #首页展示文章的数量统计countpost
    countpost = 2

    #这里x=1是根据帖子名搜索，x=2是根据标签名搜索
    if x == 2:
        k = x
        #如果输入了搜索词，则根据搜索词检索对应标签对应的帖子
        if search is not None:
            taglist = models.Tag.objects.filter(title__icontains=search).all()
            allp2tlist = []
            allpost_list = []
            for tag in taglist:
                p2tlist = models.Post2Tag.objects.filter(tag=tag)
                allp2tlist += p2tlist
            for p2t in allp2tlist:
                p_list = models.Post.objects.filter(nid=p2t.post.nid)
                allpost_list += p_list
            mywhere = "keyword=" + (search)
            countpost = len(allp2tlist)
        #如果没输入搜索词，则展示帖子为全部帖子
        else:
            allpost_list = models.Post.objects.all()
            countpost = len(allpost_list)
    elif x == 1:
        k = x
        #如果输入了搜索词，则根据搜索词检索对应的帖子
        if search is not None:
            allpost_list = models.Post.objects.filter(title__icontains=search).all()
            mywhere = "keyword=" + (search)
            countpost = len(allpost_list)
        #如果没输入搜索词，则展示帖子为全部帖子
        else:
            allpost_list = models.Post.objects.all()
            countpost = len(allpost_list)
    else:
        allpost_list = models.Post.objects.all()
        countpost = len(models.Post.objects.all())

    #对帖子进行分页，每页展示五个帖子
    allpost_list = list(reversed(allpost_list))
    p = Paginator(allpost_list, 5)
    if pindex < 1:
        pindex = 1
    if pindex > p.num_pages:
        pindex = p.num_pages
    pagerange = p.page_range
    post_list = p.page(pindex)

    #随机一贴的功能实现
    op = []
    while not op:
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost + 2)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]

    #status3为True，当前登录用户为高级权限，否则为低级权限
    status = UserInfo.objects.get(nid=request.session.get('_auth_user_id')).status
    if status == 3:
        status3 = 1
    else:
        status3 = 0

    return render(request, "index.html", locals())

# 标签搜索功能的实现
def searchtag(request):
    #分页操作
    allpost_list = models.Post.objects.all()
    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    tag_list = models.Tag.objects.all()
    return render(request, 'searchtag.html', locals())

# 注册视图
def register(request):
    if request.is_ajax():
        form = UserForm(request.POST)
        response = {"user": None, "msg": None}
        #判断表单是否合理，若合理则根据表单信息更新数据库，新建用户
        if form.is_valid():
            response["user"] = form.cleaned_data.get("user")
            user = form.cleaned_data.get("user")
            # print("user", user)
            pwd = form.cleaned_data.get("pwd")
            email = form.cleaned_data.get("email")
            avatar_obj = request.FILES.get("avatar")
            extra = {}
            if avatar_obj:
                extra["avatar"] = avatar_obj
            user_obj = UserInfo.objects.create_user(username=user, password=pwd, email=email, **extra)
            user_obj.save()
        else:
            response["msg"] = form.errors
        return JsonResponse(response)
    form = UserForm()
    return render(request, "register.html", {"form": form})



# 发帖视图
def createpost(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        # 防止xss攻击,过滤script标签
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            print(tag.name)
            if tag.name == "script":
                tag.decompose()
        #根据提交的信息建立帖子
        ob = models.Post.objects.create(title=title, content=str(soup), user=request.user)
        #判断提交的标签是否是新标签，如果是则新建，如果不是则不用新建
        tagtitle = request.POST.get("tag")
        if not models.Tag.objects.filter(title=tagtitle).all():
            currenttag = Tag()
            currenttag.title = tagtitle
            currenttag.save()
        else:
            currenttag = models.Tag.objects.filter(title=tagtitle).all()[0]
            currenttag.save()
        #建立新的Post2Tag连接
        newp2t = Post2Tag()
        newp2t.tag = currenttag
        newp2t.post = ob
        newp2t.save()
        return redirect("/index/1/1")
    return render(request, "createpost.html")


# 帖子详情页视图
def post_detail(request, username, post_id):
    #获取页面信息，用户信息等等
    user = UserInfo.objects.filter(username=username).first()
    post_obj = models.Post.objects.filter(pk=post_id).first()
    page = post_id
    comment_list = models.Comment.objects.filter(post_id=post_id)

    postlist=models.Post.objects.filter(title__icontains=post_obj.title).all()
    allp2tlist=[]
    alltaglist=[]
    for currentpost in postlist:
        p2tlist=models.Post2Tag.objects.filter(post=currentpost)
        allp2tlist+=p2tlist
    for p2t in allp2tlist:
        t_list=models.Tag.objects.filter(nid=p2t.tag.nid)
        alltaglist+=t_list

    readuserid = request.session.get('_auth_user_id')
    readuser=models.UserInfo.objects.filter(nid=readuserid)[0]
    print(readuser.nid)
    for currenttag in alltaglist:
        u2tlist=models.User2Tag.objects.filter(user=readuser,tag=currenttag)
        lenlen=len(u2tlist)
        if lenlen==0:
            newu2t=models.User2Tag()
            newu2t.user=readuser
            newu2t.tag=currenttag
            newu2t.weight=1
            newu2t.save()
            print("u2tlist==[]")
        else:
            u2tlist.update(weight=F("weight") + 1)
            print("u2tlist!=[]")

    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, "post_detail.html", locals())



# 点赞点踩功能视图
def digg(request):
    # 点赞人即当前登录人
    post_id = request.POST.get("post_id")
    #判断是点赞还是点踩
    is_up = json.loads(request.POST.get("is_up")) 
    user_id = request.user.pk
    obj = models.PostUpDown.objects.filter(user_id=user_id, post_id=post_id).first()

    #对点赞点踩表进行更新
    response = {"state": True}
    if not obj:
        ard = models.PostUpDown.objects.create(user_id=user_id, post_id=post_id, is_up=is_up)

        queryset = models.Post.objects.filter(pk=post_id)
        if is_up:
            queryset.update(up_count=F("up_count") + 1)
        else:
            queryset.update(down_count=F("down_count") + 1)
    else:
        response["state"] = False
        response["handled"] = obj.is_up
    return JsonResponse(response)


# 提交评论视图
def comment(request):
    #获取用户信息，帖子信息等等基本信息
    post_id = request.POST.get("post_id")
    pid = request.POST.get("pid")
    content = request.POST.get("content")
    user_id = request.user.pk
    post_obj = models.Post.objects.filter(pk=post_id).first()

    #评论数据库的更新
    with transaction.atomic():
        comment_obj = models.Comment.objects.create(user_id=user_id, post_id=post_id, content=content,
                                                    parent_comment_id=pid)
        models.Post.objects.filter(pk=post_id).update(comment_count=F("comment_count") + 1)

    response = {}
    response["create_time"] = comment_obj.create_time.strftime("%Y-%m-%d %X")
    response["username"] = request.user.username
    response["content"] = content
    return JsonResponse(response)

# 评论树视图，用于获取评论之间的父子关系
def get_comment_tree(request):
    post_id = request.GET.get("post_id")
    response = list(models.Comment.objects.filter(post_id=post_id).order_by("pk").values("pk", "content","parent_comment_id"))
    return JsonResponse(response, safe=False)

# 修改用户个人头像信息的视图
def modifya(request):
    if request.is_ajax():
        form = AvatarForm(request.POST, user=request.user)
        response = {"msg": None}
        if form.is_valid():
            user = request.user
            #对头像进行修改
            avatar_obj = request.FILES.get("avatar")
            print("1")
            if avatar_obj:
                print("1")
                user.avatar = avatar_obj
                user.save()
        else:
            response["msg"] = form.errors
        return JsonResponse(response)
    else:
        form = UserForm()

    allpost_list = models.Post.objects.all()
    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, "modifya.html", locals())


# 修改密码的视图
def cgpwd(request):
    if request.is_ajax():
        form = ChangePasswordForm(request.POST, user=request.user) 
        response = {"msg": None}
        #对密码进行修改
        if form.is_valid():
            user = request.user
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            #修改后自动登出账号
            auth.logout(request)
        else:
            response["msg"] = form.errors
        return JsonResponse(response)
    else:
        form = ChangePasswordForm()
    allpost_list = models.Post.objects.all()
    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, 'cgpwd.html', locals())


# 创建帖子与标签联系p2t的视图
def createp2t(request):
    if request.method == "POST":
        #获取帖子与标签的信息
        posttitle = request.POST.get("title")
        ob = models.Post.objects.filter(title=posttitle).all()[0]
        tagtitle = request.POST.get("tag")
        currenttag = Tag()
        currenttag.title = tagtitle
        currenttag.save()
        #新建p2t并更新数据库
        newp2t = Post2Tag()
        newp2t.tag = currenttag
        newp2t.post = ob
        newp2t.save()
        response = {"msg": "i"}
        return JsonResponse(response)
    return render(request, "createp2t.html")


# 具有发帖权限用户的信息视图
def clubinfo(request, username):
    #获取并展示该用户的信息
    userid = request.session.get('_auth_user_id')
    xisfollow = models.following.objects.filter(Q(club__username=username) & Q(fan__nid=userid)).first()
    currentclub = models.UserInfo.objects.filter(username=username).first()
    post_list = models.Post.objects.filter(user__username=username).all()
    allpost_list = models.Post.objects.all()

    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, "clubinfo.html", locals())


# 关注功能视图
def followta(request, clubid):
    #获取关注者、被关注者的信息
    userid = request.session.get('_auth_user_id')
    currentfan = models.UserInfo.objects.filter(nid=userid).first()
    currentidol = models.UserInfo.objects.filter(nid=clubid).first()
    currentidolusername = currentidol.username
    #更新数据库
    ob = following()
    ob.club = currentidol
    ob.fan = currentfan
    ob.save()

    return redirect('/clubinfo/%s' % (currentidolusername))


# 浏览我的关注的视图
def myidol(request):
    #获取被当前用户关注的所有用户的信息
    userid = request.session.get('_auth_user_id')
    followinglist = models.following.objects.filter(fan__nid=userid).all()
    idollist = []
    for ifollowing in followinglist:
        idollist.append(ifollowing.club)
    #进行展示
    allpost_list = models.Post.objects.all()
    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, "myidol.html", locals())


# 提交申请表的页面
def createapplication(request):
    #获取当前申请用户的基本信息
    if request.method == "POST":
        ob = Applications()
        content = request.POST.get("content")
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            print(tag.name)
            if tag.name == "script":
                tag.decompose()
        ob.content = str(soup)
        nid = request.session.get('_auth_user_id')
        user = UserInfo.objects.get(pk=nid)
        user.status = 2
        user.save()
        ob.user = user
        ob.save()
        return redirect("/index/1/1")
    nid = request.session.get('_auth_user_id')
    user = UserInfo.objects.get(pk=nid)
    status = user.status
    #申请人状态
    statuslist = [0, 0, 0, 0]
    statuslist[status - 1] = 1
    status1 = statuslist[0]
    status2 = statuslist[1]
    status3 = statuslist[2]
    status4 = statuslist[3]
    allpost_list = models.Post.objects.all()
    p = Paginator(allpost_list, 5)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    return render(request, "createapplication.html", locals())


# 热度排行视图
def hotrank(request, pindex=1):
    #根据点赞数，对帖子进行排行后展示
    allpost_list = models.Post.objects.all().order_by('-up_count')
    p = Paginator(allpost_list, 5)
    if pindex < 1:
        pindex = 1
    if pindex > p.num_pages:
        pindex = p.num_pages
    countpost = len(models.Post.objects.all())
    post_list = p.page(pindex)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    status = UserInfo.objects.get(nid=request.session.get('_auth_user_id')).status
    if status == 3:
        status3 = 1
    else:
        status3 = 0
    return render(request, "hotrank.html", locals())


# 上传函数视图
def upload(request):
    #获取用户上传的图片并保存至本地
    print(request.FILES)
    img_obj = request.FILES.get("upload_img")
    print(img_obj.name)
    path = os.path.join(settings.MEDIA_ROOT, "add_post_img", img_obj.name)
    with open(path, "wb") as f:
        for line in img_obj:
            f.write(line)
    response = {
        "error": 0,
        "url": "/media/add_post_img/%s" % img_obj.name,
    }
    return HttpResponse(json.dumps(response))


def interest(request,pindex=1):
    #根据点赞数，对帖子进行排行后展示
    userid = request.session.get('_auth_user_id')
    allpost_list = models.Post.objects.all()
    user = UserInfo.objects.filter(nid=userid).first()

    for currentpost in allpost_list:
        sum=65534
        allp2tlist=models.Post2Tag.objects.filter(post=currentpost)
        alltaglist=[]
        if allp2tlist==[]:
            currentpost.curuserweisum = sum
            currentpost.save()
            break
        for p2t in allp2tlist:
            t_list=models.Tag.objects.filter(nid=p2t.tag.nid)
            alltaglist+=t_list
            print(alltaglist)
        for currenttag in alltaglist:
            u2tlist=models.User2Tag.objects.filter(user=user,tag=currenttag)
            lenlen = len(u2tlist)
            if lenlen!= 0:
                sum-=u2tlist[0].weight
        currentpost.curuserweisum=sum
        currentpost.save()

    allpost_list = models.Post.objects.all().order_by('curuserweisum')
    p = Paginator(allpost_list, 5)
    if pindex < 1:
        pindex = 1
    if pindex > p.num_pages:
        pindex = p.num_pages
    countpost = len(models.Post.objects.all())
    post_list = p.page(pindex)
    op = []
    while not op:
        countpost = len(models.Post.objects.all())
        random.seed(datetime.now())
        rangepost_id = random.randint(1, countpost)
        op = models.Post.objects.filter(nid=rangepost_id)
    op = op[0]
    status = UserInfo.objects.get(nid=request.session.get('_auth_user_id')).status
    if status == 3:
        status3 = 1
    else:
        status3 = 0
    return render(request, "interest.html", locals())