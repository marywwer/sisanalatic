import time                                      # time - библиотека для работы с датой/временем - в основном, для протокола

from Vars import detail_protokol_file            # полный путь и имя файла, в который будет сохраняться детальный протокол, если переменная if_detail_protokol_in_file=True
from Vars import main_protokol_file              # полный путь и имя файла, в который будет сохраняться главный протокол
from Vars import json_arch_file                  # файл, в который сохранять все json-строки, полученные от ТГ-бота

def MainProtokol(s,ts = 'Предупреждение'):
    dt=time.strftime('%d.%m.%Y %H:%M:')+'00'
    
    # обработка исключений - не писать в протокол "левых" обращений - возможно это специфика хостнига NetAngels
    if 'favicon' in s: return ""
    if 'robots.txt' in s: return ""
    
    f=open(main_protokol_file,'a')
    f.write(dt+';'+str(ts)+';'+str(s)+'\n')
    f.close

def DetailProtokol(s):
    dt=time.strftime('%d.%m.%Y %H:%M:')+'00'
    
    f=open(detail_protokol_file,'a')
    f.write(dt+';'+s+'\n')
    f.close  

def SaveJsonInFile(s):
    dt=time.strftime('%d.%m.%Y %H:%M:')+'00'
    
    f=open(json_arch_file,'a')
    f.write(dt+';'+s+'\n')
    f.close