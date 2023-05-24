# 这里是对模型model的定义文件，相关模型的定义如下
# 注意，每个model都在数据库中有自己对应的位置

from django.db import models
from django.contrib.auth.models import AbstractUser

# 定义用户信息的模型
class UserInfo(AbstractUser):
    #nid是主键，唯一确定
    nid = models.AutoField(primary_key=True)
    #电话号码
    telephone = models.CharField(max_length=11, null=True, unique=True)
    #头像
    avatar = models.FileField(upload_to='avatars/', default="avatars/default.png")
    #创建时间
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    #用户的发帖权限需要向管理员申请，status表示申请状态，status=3就可以正常发帖
    status=models.IntegerField(default=1)#1未申请，2申请待审核，3审核通过，4审核未通过
    def __str__(self):
        return self.username

# 标签模型
class Tag(models.Model):
    #标签模型主键
    nid = models.AutoField(primary_key=True)
    #标签的名称
    title = models.CharField(verbose_name='标签名称', max_length=32)
    def __str__(self):
        return self.title

# 帖子模型
class Post(models.Model):
    #帖子模型主键
    nid = models.AutoField(primary_key=True)
    #帖子标题
    title = models.CharField(max_length=50, verbose_name='文章标题')
    #帖子的描述（缩略显示，便于快速把握要点）
    desc = models.CharField(max_length=255, verbose_name='文章描述')
    #帖子创建时间
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    #帖子的主体内容
    content = models.TextField()
    #评论数的统计
    comment_count = models.IntegerField(default=0)
    #点赞数的统计
    up_count = models.IntegerField(default=0)
    #点踩数的统计
    down_count = models.IntegerField(default=0)
    #发帖者的信息
    user = models.ForeignKey(verbose_name='作者', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    #帖子标签的信息
    tags = models.ManyToManyField(
        to="Tag",
        through='Post2Tag',
        through_fields=('post', 'tag'),
    )
    curuserweisum=models.IntegerField(default=65535)

    def __str__(self):
        return self.title

# 由于标签和帖子是多对多的关系，因此需要一个专门的连接model，Post2Tag
# 用于建立贴子与标签的关系，以下注释简称p2t
class Post2Tag(models.Model):
    #p2t的主键值
    nid = models.AutoField(primary_key=True)
    #帖子的信息
    post = models.ForeignKey(verbose_name='文章', to="Post", to_field='nid', on_delete=models.CASCADE)
    #标签的信息
    tag = models.ForeignKey(verbose_name='标签', to="Tag", to_field='nid', on_delete=models.CASCADE)
    class Meta:
        unique_together = [
            ('post', 'tag'),
        ]
    def __str__(self):
        v = self.post.title + "---" + self.tag.title
        return v

# 用于记录对特定帖子的赞踩数目类型
class PostUpDown(models.Model):
    #赞踩数的主键
    nid = models.AutoField(primary_key=True)
    #点赞或点踩的用户
    user = models.ForeignKey('UserInfo', null=True, on_delete=models.CASCADE)
    #被点赞或点踩的帖子
    post = models.ForeignKey("Post", null=True, on_delete=models.CASCADE)
    #判断点赞还是点踩，True为赞，False为踩
    is_up = models.BooleanField(default=True)
    class Meta:
        unique_together = [
            ('post', 'user'),
        ]


# 对帖子的评论
class Comment(models.Model):
    #评论的主键
    nid = models.AutoField(primary_key=True)
    #被评论的文章信息
    post = models.ForeignKey(verbose_name='评论文章', to='Post', to_field='nid', on_delete=models.CASCADE)
    #评论者的信息
    user = models.ForeignKey(verbose_name='评论者', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    #评论的内容
    content = models.CharField(verbose_name='评论内容', max_length=255)
    #评论的时间
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    #父评论（因为有追评功能）
    parent_comment = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
    def __str__(self):
        return self.content


# 关注表
class following(models.Model):
    #关注类型的主键
    nid = models.AutoField(primary_key=True)
    #被关注者的信息
    club = models.ForeignKey('UserInfo', null=True, on_delete=models.CASCADE,related_name="club")
    #关注者的信息
    fan = models.ForeignKey("UserInfo", null=True, on_delete=models.CASCADE,related_name="fan")


# 用户想要成为发帖人，需要向后台管理者申请，这是申请表类型
class Applications(models.Model):
    #申请表主键
    nid = models.AutoField(primary_key=True)
    #申请者信息
    user = models.ForeignKey(verbose_name='申请人', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    #申请理由
    content = models.CharField(verbose_name='申请理由', max_length=255)
    #申请时间
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    def __str__(self):
        return self.content




# 用户与标签关系表
class User2Tag(models.Model):
    #u2t主键
    nid = models.AutoField(primary_key=True)
    #被关注者的信息
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', to_field='nid', on_delete=models.CASCADE)
    #标签的信息
    tag = models.ForeignKey(verbose_name='标签', to="Tag", to_field='nid', on_delete=models.CASCADE)
    #数目统计权重
    weight = models.IntegerField(default=0)