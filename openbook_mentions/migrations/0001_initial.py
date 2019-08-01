# Generated by Django 2.2.3 on 2019-07-31 17:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('openbook_posts', '0037_merge_20190702_1206'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostUserMention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_mentions', to='openbook_posts.Post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_mentions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PostCommentUserMention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_mentions', to='openbook_posts.PostComment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comment_mentions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]