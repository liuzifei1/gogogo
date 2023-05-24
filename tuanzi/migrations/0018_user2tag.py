# Generated by Django 3.2.13 on 2023-05-23 10:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tuanzi', '0017_alter_userinfo_first_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User2Tag',
            fields=[
                ('nid', models.AutoField(primary_key=True, serialize=False)),
                ('weight', models.IntegerField(default=0)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tuanzi.tag', verbose_name='标签')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
        ),
    ]
