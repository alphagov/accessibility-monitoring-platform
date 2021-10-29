# Generated by Django 3.2.8 on 2021-10-29 14:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cases', '0017_remove_case_service_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
                ('date_of_test', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, default='')),
                ('screen_size', models.CharField(choices=[('15in', '15 inch'), ('13in', '13 inch')], default='15in', max_length=20)),
                ('is_exemption', models.CharField(choices=[('yes', 'Yes'), ('no', 'No'), ('unknown', 'Unknown')], default='unknown', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('type', models.CharField(choices=[('initial', 'Initial'), ('eq-retest', 'Equality body retest')], default='initial', max_length=20)),
                ('check_metadata_complete_date', models.DateField(blank=True, null=True)),
                ('check_pages_complete_date', models.DateField(blank=True, null=True)),
                ('check_manual_complete_date', models.DateField(blank=True, null=True)),
                ('check_axe_complete_date', models.DateField(blank=True, null=True)),
                ('check_pdf_complete_date', models.DateField(blank=True, null=True)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='check_case', to='cases.case')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='WcagTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('manual', 'Manual'), ('axe', 'Axe'), ('pdf', 'PDF')], default='pdf', max_length=20)),
                ('name', models.TextField(blank=True, default='')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('extra', 'Page'), ('home', 'Home page'), ('contact', 'Contact page'), ('statement', 'Accessibility statement'), ('pdf', 'PDF'), ('form', 'A form')], default='extra', max_length=20)),
                ('name', models.TextField(blank=True, default='')),
                ('url', models.TextField(blank=True, default='')),
                ('not_found', models.CharField(choices=[('no', 'No'), ('yes', 'Yes')], default='no', max_length=20)),
                ('parent_check', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='page_check', to='checks.check')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='CheckTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('manual', 'Manual'), ('axe', 'Axe'), ('pdf', 'PDF')], default='pdf', max_length=20)),
                ('failed', models.CharField(choices=[('no', 'No'), ('yes', 'Yes')], default='no', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('parent_check', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_check', to='checks.check')),
                ('wcag_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_wcagtest', to='checks.wcagtest')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
