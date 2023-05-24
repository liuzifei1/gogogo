# 代码运行的总入口，在cmd命令行中使用python manage.py runserver命令来运行项目
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xiaotuan.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
    
if __name__ == '__main__':
    main()
