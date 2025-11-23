import time                                      # time - библиотека для работы с датой/временем - в основном, для протокола
from urllib.parse import parse_qsl               # urllib.parse import parse_qsl - для распарсивания полей, переданных из форм с сайтов
import psycopg2                                  # библиотека для работы с PostgreSQL

import json
import requests

from protokol import MainProtokol
from protokol import DetailProtokol
from protokol import SaveJsonInFile
from Vars import detail_protokol_file            # полный путь и имя файла, в который будет сохраняться детальный протокол, если переменная if_detail_protokol_in_file=True
from Vars import main_protokol_file              # полный путь и имя файла, в который будет сохраняться главный протокол
from Vars import if_detail_protokol_on_screen    # True - выводить детальный протокол на экран. ! html-файлы, предусмотренные процессом - не выводятся
from Vars import if_detail_protokol_in_file      # True - писать детальный протокол в файл детального протокола, определенный в переменной detail_protokol_file
from Vars import token                           # токен телеграмм-бота

from Vars import user_name                       # параметр подключения к БД PostgreSQL :: имя пользователя
from Vars import passwd                          # параметр подключения к БД PostgreSQL :: пароль
from Vars import host_name                       # параметр подключения к БД PostgreSQL :: IP или URL адрес хоста
from Vars import port_id                         # параметр подключения к БД PostgreSQL :: порт подключения к БД
from Vars import database_name                   # параметр подключения к БД PostgreSQL :: имя БД


def application(env, start_response):
    try:
        if if_detail_protokol_in_file: DetailProtokol('----------------------------------------------------------------------------------')
        
        if if_detail_protokol_on_screen:
            content='''<html>
                            <head>
                                <meta charset="utf-8" />
                                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                            </head>
                            <body>'''
        else:
            content=''
        
        regim=''
        
        k=list(env.keys())
        
        for key in k:
            if str(key).upper() == 'PATH_INFO':
                if env[key] == '/tg_bot':
                    regim='tg_bot'
                elif env[key] == '/':
                    regim='main_page'
                    #content='Ooops ....'
                    #start_response('200 OK', [('Content-Type','text/html')])
                    #return [content.encode('utf-8')]
                elif env[key] == '/site_vote':
                    regim='site_vote'
                elif env[key] == '/site_note':
                    regim='site_note'
                elif env[key] == '/klass_graph':
                    regim='klass_graph'
                elif env[key] == '/one_graph':
                    regim='one_graph'
                elif env[key] == '/log0.csv':
                    with open(detail_protokol_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    start_response('200 OK', [('Content-Type','text/html')])
                    return [content.encode('utf-8')]
                else:
                    raise ValueError('Вызов неизвестного URL в WSGI :: '+env[key]+' :: '+str(env['REMOTE_ADDR']))
        
        query_string=''
        wsgi_input=''
        filters=''
        
        # разбор всех параметров, переданных в скрипт по "протоколу" WSGI
        for key in k:
            if if_detail_protokol_on_screen: content=content+'<p>'+str(key)+'-->'+str(env[key])+'</p>'
            if if_detail_protokol_in_file: DetailProtokol(str(key)+';'+str(env[key]))
            
            if str(key).upper() == 'QUERY_STRING': query_string=env[key]
            if str(key).lower() == 'wsgi.input': wsgi_input=env[key].read()
        
        # разбор параметров
        if query_string!='':
            # разбор конкретных параметров
            
            id_graph=''     # id графика, за который голосуют
            id_voice=''     # код голосования
            note=''         # текст заметки
            id_klass=''     # id выбранной классификации
            regim_klass=''  # режим классификации (1 - установить, 0 - снять)
            
            x=parse_qsl(query_string,encoding='utf-8')
        
            for y in x:
                if if_detail_protokol_on_screen: content=content+'<p>'+str(y[0])+'-->'+str(y[1])+'</p>'
                if if_detail_protokol_in_file: DetailProtokol(y[0]+';'+str(y[1]))
                
                if y[0].lower()=='id_graph': id_graph=y[1]
                if y[0].lower()=='id_voice': id_voice=y[1]
                if y[0].lower()=='note': note=y[1]
                if y[0].lower()=='id_klass': id_klass=y[1]
                if y[0].lower()=='regim_klass': regim_klass=y[1]
                if y[0].lower()=='filters': filters=json.loads(y[1])
        
        if regim=='tg_bot':    
            # это код - обработчик всего, что приходит от чат-бота    
            x=wsgi_input.decode('UTF-8')
            y=x.replace('\n',' ')
            y=x.replace("'","")
                
            try:
                z=json.loads(y)
                SaveJsonInFile(str(z))
            except:
                raise ValueError('Не удалось распарсить в JSON полученную строку')
                
            update_id=z['update_id']
            chat_id=z['message']['chat']['id']
            from_first_name=''
            if 'first_name' in z['message']['from']: from_first_name=z['message']['from']['first_name']
            from_second_name=''
            if 'last_name' in z['message']['from']: from_second_name=z['message']['from']['last_name']
            from_username=''
            if 'username' in z['message']['from']: from_username=z['message']['from']['username']
            
            message_date=z['message']['date']
            message_dt=time.strftime('%d.%m.%Y %H:%M:',time.gmtime(message_date))+'00'
            
            file_name=''
            file_name_html=''
            file_id=''
            if_photo=False
            
            if 'photo' in z['message']:
                if_photo=True
                file_id=z['message']['photo'][len(z['message']['photo'])-1]['file_id']
                file_name='../www/'+str(update_id)+'_'+str(message_date)+'.jpg'
                file_name_html=str(update_id)+'_'+str(message_date)+'.jpg'
                    
                response = requests.get('https://api.telegram.org/bot'+token+'/getFile?file_id='+file_id)
                if response:
                    response_dict=response.json()
                    file_path=response_dict['result']['file_path']
                    #if response.status_code == 200:

                    file_resp=requests.get('https://api.telegram.org/file/bot'+token+'/'+file_path)
                    if file_resp:
                        with open(file_name,'wb') as new_file:
                             new_file.write(file_resp.content)
                    else:
                        raise ValueError('Не удалось скачать файл')
                else:
                    raise ValueError('Не удалось получить ссылку на файл')
            else:
                send_message=requests.get('https://api.telegram.org/bot'+token+'/sendMessage?&chat_id='+str(chat_id)+'&text=(!) в бот не передана картинка (!) тексты и команды пока не обрабатываются НО в протокол фиксируются ;-)')
                if not send_message: raise ValueError('Не удалось отправить текст в бот :: (!) в бот не передана картинка (!) тексты и команды пока не обрабатываются')
            
            caption=''
            if 'caption' in z['message']: caption=z['message']['caption']
            caption_url=''
            if 'caption_entities' in z['message']:
                for x in range(len(z['message']['caption_entities'])):
                    if 'url' in z['message']['caption_entities'][x]:
                        caption_url=z['message']['caption_entities'][x]['url']
                
            message_text=''
            if 'text' in z['message']: message_text=z['message']['text']
            message_type=''
            if 'entities' in z['message']: 
                for x in range(len(z['message']['entities'])): 
                    if 'type' in z['message']['entities'][x]: message_type=z['message']['entities'][x]['type'] 
            
            forward_from_chat=''
            forward_from_chat_name=''
            forward_from_chat_type=''
            if 'forward_from_chat' in z['message']:
                forward_from_chat=z['message']['forward_from_chat']['title']
                forward_from_chat_name=z['message']['forward_from_chat']['username']
                forward_from_chat_type=z['message']['forward_from_chat']['type']
                
            if if_photo:
                try:
                    connection = psycopg2.connect(user=user_name,
                                                  password=passwd,
                                                  host=host_name,
                                                  port=port_id,
                                                  database=database_name)
                    cursor = connection.cursor()
                    
                    insert_query = "INSERT INTO refdash \
                                    (update_id, \
                                     chat_id, \
                                     from_first_name, \
                                     from_second_name, \
                                     from_username, \
                                     message_date, \
                                     file_name, \
                                     caption, \
                                     caption_url, \
                                     message_text, \
                                     message_type,\
                                     forward_from_chat, \
                                     forward_from_chat_name, \
                                     forward_from_chat_type, \
                                     file_id, \
                                     chat_bot, \
                                     dt) VALUES ("
                    insert_query = insert_query+"'"+str(update_id)+"',"
                    insert_query = insert_query+"'"+str(chat_id)+"',"
                    insert_query = insert_query+"'"+str(from_first_name)+"',"
                    insert_query = insert_query+"'"+str(from_second_name)+"',"
                    insert_query = insert_query+"'"+str(from_username)+"',"
                    insert_query = insert_query+"'"+str(message_date)+"',"
                    insert_query = insert_query+"'"+str(file_name_html)+"',"
                    insert_query = insert_query+"'"+str(caption)+"',"
                    insert_query = insert_query+"'"+str(caption_url)+"',"
                    insert_query = insert_query+"'"+str(message_text)+"',"
                    insert_query = insert_query+"'"+str(message_type)+"',"
                    insert_query = insert_query+"'"+str(forward_from_chat)+"',"
                    insert_query = insert_query+"'"+str(forward_from_chat_name)+"',"
                    insert_query = insert_query+"'"+str(forward_from_chat_type)+"',"
                    insert_query = insert_query+"'"+str(file_id)+"',"
                    insert_query = insert_query+"'test_chat_bot',"
                    insert_query = insert_query+"now()+ interval '5 hour')"
                    
                    DetailProtokol(insert_query)
                    cursor.execute(insert_query)
                    connection.commit() 
                    
                    cursor.execute("SELECT COUNT(id) from refdash where file_name is not null")
                    connection.commit()
                    record = cursor.fetchall()
                    dash_count=record[0][0]   # количество дашбордов
                    
                    send_message=requests.get('https://api.telegram.org/bot'+token+'/sendMessage?&chat_id='+str(chat_id)+'&text=Отлично ! картинка принята. Всего дашбордов в базе : '+str(dash_count))
                    if not send_message: raise ValueError('Не удалось отправить текст в бот :: Отлично ! картинка принята')
                except Exception as S:
                    send_message=requests.get('https://api.telegram.org/bot'+token+'/sendMessage?&chat_id='+str(chat_id)+'&text=(!) ОШИБКА СОХРАНЕНИЯ В БД (!)')
                    raise ValueError('ОШИБКА СОХРАНЕНИЯ В БД '+str(S))
                finally:
                    if connection:
                        cursor.close()
                        connection.close()
        elif regim=='main_page':
            # Это код отображения главной страницы
            try:
                with open('main_head.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as S:
                raise ValueError('ОШИБКА чтения файла для главной страницы main_head.txt '+str(S))
            
            try:
                connection = psycopg2.connect(user=user_name,
                                              password=passwd,
                                              host=host_name,
                                              port=port_id,
                                              database=database_name)
                cursor = connection.cursor()
                
                cursor.execute("SELECT COUNT(id) from refdash where file_name is not null")
                connection.commit()
                record = cursor.fetchall()
                dash_count=record[0][0]   # количество дашбордов
            
                content=content.replace('{{count}}',str(dash_count))
                
                # блок добавления кнопок фильтрации
                connection2 = psycopg2.connect(user=user_name,
                              password=passwd,
                              host=host_name,
                              port=port_id,
                              database=database_name)
                cursor2 = connection2.cursor()
                
                cursor2.execute("SELECT DISTINCT id_type FROM klass_spr ORDER BY id_type")
                connection2.commit()
                record1 = cursor2.fetchall()
                
                filter_div="""<div style="display:inline-block">
                                <a onclick="set_filter(100);"><div id="filter_100" class="klass_set" style="pointer-events: none;">ТОП</div></a>
                                <a onclick="set_filter(200);"><div id="filter_200" class="klass_set" style="pointer-events: none;">ДичЪ</div></a>
                                <a onclick="set_filter(300);"><div id="filter_300" class="klass_set">Без класс</div></a>
                                <a onclick="set_filter(400);"><div id="filter_400" class="klass_set">С заметками</div></a>
                              </div>
                              <hr>
                            """
                
                for tt in range(len(record1)):
                    filter_div=filter_div+'<div style="display:inline-block">'+chr(13)
                    #cursor2.execute("""SELECT a.id_klass,a.klass_name FROM klass_spr a WHERE a.id_type="""+str(record1[tt][0])+"""  ORDER BY sort_order """)
                    cursor2.execute("""SELECT a.id_klass,a.klass_name,count(*) 
                                          FROM klass_spr a left join klass b on a.id_klass=b.id_klass 
                                          WHERE a.id_type="""+str(record1[tt][0])+""" group by a.id_klass,a.klass_name """)
                    connection2.commit()
                    record2 = cursor2.fetchall()
                    
                    for xx in range(len(record2)):
                        klass_type='klass_set'
                        if "filter_"+str(record2[xx][0]) in filters:
                            if filters["filter_"+str(record2[xx][0])] == 1:
                                klass_type='klass_unset'
                            if filters["filter_"+str(record2[xx][0])] == 0:
                                klass_type='klass_set'
                        
                        filter_div=filter_div+'<a onclick="set_filter('+str(record2[xx][0])+');"><div id="filter_'+str(record2[xx][0])+'" class="'+klass_type+'">'+str(record2[xx][1])+'  [ '+str(record2[xx][2])+' ]</div></a>'
                    
                    filter_div=filter_div+'</div><hr>'+chr(13)
                
                filter_div=filter_div+"""<p align="left">
                                            <a class="button15" onclick="show_filters();">Применить фильтры</a>
                                        </p>
                                        <hr>"""
                                        
                content=content.replace('{{filter}}',str(filter_div))
                
                try:
                    with open('main_table.txt', 'r', encoding='utf-8') as f:
                        content_table = f.read()
                except Exception as S:
                        raise ValueError('ОШИБКА чтения файла main_table.txt '+str(S))
                
                # первый неоптимальный код
                sql_text="SELECT  message_date,\
                                        file_name,\
                                        from_first_name,\
                                        from_second_name,\
                                        from_username,\
                                        caption,\
                                        forward_from_chat_name,\
                                        forward_from_chat_type,\
                                        forward_from_chat,\
                                        caption_url, \
                                        id, \
                                        (select count(id) from voices where voices.id_graph=refdash.id and voices.voice=1) as v1, \
                                        (select count(id) from voices where voices.id_graph=refdash.id and voices.voice=2) as v2, \
                                        (select count(id) from voices where voices.id_graph=refdash.id and voices.voice=3) as v3, \
                                        (select count(id) from notes where notes.id_graph=refdash.id) as notes \
                                from refdash where file_name is not null order by dt desc"
                
                # оптимальный код от Никиты Смиренина
                sql_text="""
                            SELECT {{top}} refdash.message_date,
                                    refdash.file_name,
                                    refdash.from_first_name,
                                    refdash.from_second_name,
                                    refdash.from_username,
                                    refdash.caption,
                                    refdash.forward_from_chat_name,
                                    refdash.forward_from_chat_type,
                                    refdash.forward_from_chat,
                                    refdash.caption_url, 
                                    refdash.id, 
                                    COUNT(DISTINCT CASE WHEN voices.voice=1 THEN voices.id END) as v1,
                                    COUNT(DISTINCT CASE WHEN voices.voice=2 THEN voices.id END) as v2,
                                    COUNT(DISTINCT CASE WHEN voices.voice=3 THEN voices.id END) as v3,
                                    COUNT(DISTINCT notes.id) as notes
                            FROM refdash 
                            LEFT JOIN voices ON refdash.id = voices.id_graph
                            LEFT JOIN notes ON refdash.id = notes.id_graph
                            WHERE refdash.file_name is not null {{filter_and}} {{filter_or}}
                            GROUP BY refdash.message_date,
                                     refdash.file_name,
                                     refdash.from_first_name,
                                     refdash.from_second_name,
                                     refdash.from_username,
                                     refdash.caption,
                                     refdash.forward_from_chat_name,
                                     refdash.forward_from_chat_type,
                                     refdash.forward_from_chat,
                                     refdash.caption_url, 
                                     refdash.id
                            ORDER BY  {{order_by}}
                      """
                # разбор фильтров
                cursor2.execute("SELECT DISTINCT id_type FROM klass_spr ORDER BY id_type")
                connection2.commit()
                record1 = cursor2.fetchall()
                    
                cursor2.execute("SELECT MAX(id_klass) FROM klass_spr")
                connection2.commit()
                record2 = cursor2.fetchall()
                
                filters_in=[0]*(record2[0][0]+1)
 
                filter_and=""
                filter_or=""
                order_by="refdash.message_date DESC"
                top=""
                
                for key in filters:
                    kkey=key.split("_",1)
                    if int(kkey[1])<100: 
                        filters_in[int(kkey[1])]=filters[key]
                
                sql_text=sql_text.replace('{{top}}',top)
                sql_text=sql_text.replace('{{filter_and}}',filter_and)
                sql_text=sql_text.replace('{{filter_or}}',filter_or)
                sql_text=sql_text.replace('{{order_by}}',order_by)
                
                # конец разбора фильтров
                
                cursor.execute(sql_text)
                                
                connection.commit()
                record = cursor.fetchall()
                
                for x in range(len(record)):
                    message_date=time.strftime('%d.%m.%Y %H:%M',time.gmtime(int(record[x][0])))
                    file_name=record[x][1]
                    from_first_name=record[x][2]
                    from_second_name=record[x][3]
                    from_username=record[x][4]
                    caption=record[x][5]
                    forward_from_chat_name=record[x][6]
                    forward_from_chat_type=record[x][7]
                    forward_from_chat=record[x][8]
                    caption_url=record[x][9]
                    id_graph=record[x][10]
                    v1=record[x][11]
                    v2=record[x][12]
                    v3=record[x][13]
                    nnotes=record[x][14]
                    
                    t=content_table.replace('{{message_date}}',str(message_date))
                    t=t.replace('{{file_name}}',file_name)
                    t=t.replace('{{#}}',str(x+1))
                    t=t.replace('{{from_first_name}}',from_first_name)
                    t=t.replace('{{from_second_name}}',from_second_name)
                    t=t.replace('{{from_username}}',from_username)
                    t=t.replace('{{caption}}',caption)
                    t=t.replace('{{forward_from_chat_name}}',forward_from_chat_name)
                    t=t.replace('{{forward_from_chat_type}}',forward_from_chat_type)
                    t=t.replace('{{forward_from_chat}}',forward_from_chat)
                    t=t.replace('{{id_graph}}',str(id_graph))
                    t=t.replace('{{v1}}',str(v1))
                    t=t.replace('{{v2}}',str(v2))
                    t=t.replace('{{v3}}',str(v3))
                    
                    
                    if caption_url=='':
                        t=t.replace('{{caption_url}}','')
                    else:
                        t=t.replace('{{caption_url}}','<a href="'+str(caption_url)+'" target="_blank"><font size="2">Прямая ссылка</font></a>')
                    #<a href="{{caption_url}}"><font size="2">Прямая ссылка</font></a>
                    
                    # блок добавления заметок
                    
                    if nnotes==0:
                        # нет заметок
                        notes="""<ul id="notes">
                                    <li>
                                          <p align="left">Новая заметка</p>
                                          <p>
                                            <form>
                                                <textarea name="comment" cols="30" rows="7" id="{{id_graph}}_note" style="border:0;"></textarea>
                                            </form>
                                          </p>
                                          <p align="center">
                                            <a class="button15" onclick="notice({{id_graph}});">Сохранить</a>
                                          </p>
                                      </li>   
                                </ul>"""
                        
                    else:
                        notes='<ul id="notes">'
                        
                        cursor2.execute("SELECT notes FROM notes WHERE id_graph="+str(id_graph)+" order by dt")
                        connection2.commit()
                        record2 = cursor2.fetchall()
                        
                        for xx in range(len(record2)):
                            notes=notes+"<li><p>"+str(record2[xx][0])+"</p></li>"
                            
                        notes=notes+"""<li>
                                          <p align="left">Новая заметка</p>
                                          <p>
                                            <form>
                                                <textarea name="comment" cols="30" rows="7" id="{{id_graph}}_note" style="border:0;"></textarea>
                                            </form>
                                          </p>
                                          <p align="center">
                                            <a class="button15" onclick="notice({{id_graph}});">Сохранить</a>
                                          </p>
                                      </li>   
                                </ul>"""
                    t=t.replace('{{notes}}',notes)
                    t=t.replace('{{id_graph}}',str(id_graph))
                    
                    # блок добавления кнопок классификации
                    
                    filters_gr=[0]*(len(filters_in))
                    
                    klass=''
                    klass_type='klass_set'
                    klass_n=0
                    
                    for tt in range(len(record1)):
                        klass=klass+'<div style="display:inline-block">'+chr(13)
                        cursor2.execute("""SELECT a.id_klass,a.klass_name,(case when b.id_graph is null then 0 else 1 end) as b 
                            FROM 
                               klass_spr a 
                               LEFT JOIN klass b ON a.id_klass=b.id_klass AND b.id_graph="""+str(id_graph)+""" where a.id_type="""+str(record1[tt][0])+"""  ORDER BY sort_order """)
                        connection2.commit()
                        record2 = cursor2.fetchall()
                        
                        for xx in range(len(record2)):
                            if int(record2[xx][2]) == 1:
                                klass_type='klass_unset'
                                filters_gr[int(record2[xx][0])] = 1
                                klass_n=klass_n+1
                            if int(record2[xx][2]) == 0:
                                klass_type='klass_set'
                                filters_gr[int(record2[xx][0])] = 0
                            
                            if filters_in[int(record2[xx][0])] == 0:
                                filters_gr[int(record2[xx][0])] = 0
                            
                            klass=klass+'<a onclick="set_klass('+str(id_graph)+','+str(record2[xx][0])+');"><div id="klass_'+str(id_graph)+'_'+str(record2[xx][0])+'" class="'+klass_type+'">'+str(record2[xx][1])+'</div></a>'
                        
                        klass=klass+'</div><hr>'+chr(13)
                        
                    t=t.replace('{{klass}}',klass)
                    
                    # финализация блока с графиком
                    if filters_in == filters_gr:
                        if "filter_300" in filters:
                            if filters["filter_300"]==1 and klass_n==0:
                                content=content+'\n'+t+'\n'
                        else:
                            if "filter_400" in filters:
                                if filters["filter_400"]==1 and nnotes>0:
                                    content=content+'\n'+t+'\n'
                            else:
                                content=content+'\n'+t+'\n'
            except Exception as S:
                raise ValueError('ОШИБКА РАБОТЫ с В БД '+str(S))
            finally:
                if connection:
                    cursor.close()
                    connection.close()
            
            #content=content+"""\n<!-- Yandex.Metrika informer --> <a href="https://metrika.yandex.ru/stat/?id=93552466&amp;from=informer" target="_blank" rel="nofollow"><img src="https://informer.yandex.ru/informer/93552466/3_0_FFFFFFFF_EFEFEFFF_1_uniques" style="width:88px; height:31px; border:0;" alt="Яндекс.Метрика" title="Яндекс.Метрика: данные за сегодня (просмотры, визиты и уникальные посетители)" class="ym-advanced-informer" data-cid="93552466" data-lang="ru" /></a> <!-- /Yandex.Metrika informer --> <!-- Yandex.Metrika counter --> <script type="text/javascript" > (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)}; m[i].l=1*new Date(); for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }} k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}) (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym"); ym(93552466, "init", { clickmap:true, trackLinks:true, accurateTrackBounce:true, webvisor:true }); </script> <noscript><div><img src="https://mc.yandex.ru/watch/93552466" style="position:absolute; left:-9999px;" alt="" /></div></noscript> <!-- /Yandex.Metrika counter -->\n"""
            content=content+'\n</body>\n</html>'
        elif regim=='one_graph': 
            if int(id_graph)<0:
                raise ValueError('ОШИБКА для отображения одного графика передан некорректный id_graph='+str(id_graph))
            
            try:
                with open('one_graph.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as S:
                raise ValueError('ОШИБКА чтения файла для главной страницы one_graph.txt '+str(S))
            
            sql_text="""
                            SELECT  refdash.message_date,
                                    refdash.file_name,
                                    refdash.from_first_name,
                                    refdash.from_second_name,
                                    refdash.from_username,
                                    refdash.caption,
                                    refdash.forward_from_chat_name,
                                    refdash.forward_from_chat_type,
                                    refdash.forward_from_chat,
                                    refdash.caption_url, 
                                    refdash.id, 
                                    COUNT(DISTINCT CASE WHEN voices.voice=1 THEN voices.id END) as v1,
                                    COUNT(DISTINCT CASE WHEN voices.voice=2 THEN voices.id END) as v2,
                                    COUNT(DISTINCT CASE WHEN voices.voice=3 THEN voices.id END) as v3,
                                    COUNT(DISTINCT notes.id) as notes
                            FROM refdash 
                            LEFT JOIN voices ON refdash.id = voices.id_graph
                            LEFT JOIN notes ON refdash.id = notes.id_graph
                            WHERE refdash.id={{id_graph}}
                            GROUP BY refdash.message_date,
                                     refdash.file_name,
                                     refdash.from_first_name,
                                     refdash.from_second_name,
                                     refdash.from_username,
                                     refdash.caption,
                                     refdash.forward_from_chat_name,
                                     refdash.forward_from_chat_type,
                                     refdash.forward_from_chat,
                                     refdash.caption_url, 
                                     refdash.id
                      """
                      
            sql_text=sql_text.replace('{{id_graph}}',id_graph)
            
            connection = psycopg2.connect(user=user_name,
                                              password=passwd,
                                              host=host_name,
                                              port=port_id,
                                              database=database_name)
            cursor = connection.cursor()
            
            cursor.execute(sql_text)
                                
            connection.commit()
            record = cursor.fetchall()
            
            for x in range(len(record)):
                message_date=time.strftime('%d.%m.%Y %H:%M',time.gmtime(int(record[x][0])))
                file_name=record[x][1]
                from_first_name=record[x][2]
                from_second_name=record[x][3]
                from_username=record[x][4]
                caption=record[x][5]
                forward_from_chat_name=record[x][6]
                forward_from_chat_type=record[x][7]
                forward_from_chat=record[x][8]
                caption_url=record[x][9]
                id_graph=record[x][10]
                v1=record[x][11]
                v2=record[x][12]
                v3=record[x][13]
                nnotes=record[x][14]
                
                t=content.replace('{{message_date}}',str(message_date))
                t=t.replace('{{file_name}}',file_name)
                t=t.replace('{{#}}',str(x+1))
                t=t.replace('{{from_first_name}}',from_first_name)
                t=t.replace('{{from_second_name}}',from_second_name)
                t=t.replace('{{from_username}}',from_username)
                t=t.replace('{{caption}}',caption)
                t=t.replace('{{forward_from_chat_name}}',forward_from_chat_name)
                t=t.replace('{{forward_from_chat_type}}',forward_from_chat_type)
                t=t.replace('{{forward_from_chat}}',forward_from_chat)
                t=t.replace('{{id_graph}}',str(id_graph))
                t=t.replace('{{v1}}',str(v1))
                t=t.replace('{{v2}}',str(v2))
                t=t.replace('{{v3}}',str(v3))
                
                
                if caption_url=='':
                    t=t.replace('{{caption_url}}','')
                else:
                    t=t.replace('{{caption_url}}','<a href="'+str(caption_url)+'" target="_blank"><font size="2">Прямая ссылка</font></a>')
                
                content=t+'\n</body>\n</html>'
        elif regim=='site_note': 
            # это код обработки заметок с сайта
            if note!="":
                try:
                    connection = psycopg2.connect(user=user_name,
                                                  password=passwd,
                                                  host=host_name,
                                                  port=port_id,
                                                  database=database_name)
                    cursor = connection.cursor()
                    
                    insert_query = "INSERT INTO notes \
                                    (id_graph, \
                                     notes, \
                                     source, \
                                     dt) VALUES ("
                    insert_query = insert_query+"'"+str(id_graph)+"',"
                    insert_query = insert_query+"'"+str(note)+"',"
                    insert_query = insert_query+"'site',"
                    insert_query = insert_query+"now()+ interval '5 hour')"
                    
                    DetailProtokol(insert_query)
                    cursor.execute(insert_query)
                    connection.commit() 
                
                    content="Заметка успешно сохранена"
                except Exception as S:
                    raise ValueError('Ошибка сохранения заметки в БД :: id_graph='+str(id_graph)+' :: notice='+str(note)+' :: '+str(S))
                finally:
                    if connection:
                        cursor.close()
                        connection.close()
            else:
                content="Пустые заметки не сохраняются"
            
            start_response('200 OK', [('Content-Type','text/html')])
            return [content.encode('utf-8')]
        elif regim=='site_vote': 
            # это код обработки голосования с сайта
            try:
                connection = psycopg2.connect(user=user_name,
                                              password=passwd,
                                              host=host_name,
                                              port=port_id,
                                              database=database_name)
                cursor = connection.cursor()
                
                insert_query = "INSERT INTO voices \
                                (id_graph, \
                                 voice, \
                                 source, \
                                 dt) VALUES ("
                insert_query = insert_query+"'"+str(id_graph)+"',"
                insert_query = insert_query+"'"+str(id_voice)+"',"
                insert_query = insert_query+"'site',"
                insert_query = insert_query+"now()+ interval '5 hour')"
                
                cursor.execute(insert_query)
                connection.commit() 
                
                cursor.execute("SELECT COUNT(*) from voices where id_graph="+str(id_graph)+" and voice="+str(id_voice))
                connection.commit()
                record = cursor.fetchall()
                content=str(record[0][0])   # количество голосов типа id_voice
            except Exception as S:
                raise ValueError('Ошибка сохранения голоса в БД :: id_graph='+str(id_graph)+' :: id_voice='+str(id_voice)+' :: '+str(S))
            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    
            start_response('200 OK', [('Content-Type','text/html')])
            return [content.encode('utf-8')]
        elif regim=='klass_graph':
            # это код обработки классификации графика с сайта
            try:
                connection = psycopg2.connect(user=user_name,
                                              password=passwd,
                                              host=host_name,
                                              port=port_id,
                                              database=database_name)
                cursor = connection.cursor()
                
                if regim_klass=="1":
                    insert_query = "INSERT INTO klass \
                                    (id_graph, \
                                     id_klass, \
                                     source, \
                                     dt) VALUES ("
                    insert_query = insert_query+"'"+str(id_graph)+"',"
                    insert_query = insert_query+"'"+str(id_klass)+"',"
                    insert_query = insert_query+"'site',"
                    insert_query = insert_query+"now()+ interval '5 hour')"
                    
                    cursor.execute(insert_query)
                    connection.commit() 
                
                    content='ok'
                elif regim_klass=="0":
                    insert_query = "DELETE FROM klass WHERE id_graph="+str(id_graph)+" AND id_klass="+str(id_klass)
                    
                    cursor.execute(insert_query)
                    connection.commit() 
                
                    content='ok'
                else:
                    MainProtokol('Передан неизвестный режим изменения классификации regim_klass='+str(regim_klass)+" его тип "+str(type(regim_klass)),'Ошибка')
            except Exception as S:
                raise ValueError('Ошибка сохранения классификации в БД :: id_graph='+str(id_graph)+' :: id_klass='+str(id_klass)+' :: '+str(S))
            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    
            start_response('200 OK', [('Content-Type','text/html')])
            return [content.encode('utf-8')]
        else:
            if if_detail_protokol_in_file: DetailProtokol('regim = '+str(regim))
            
            start_response('200 OK', [('Content-Type','text/html')])
            return [content.encode('utf-8')]
                
        # fin завершение основной процедуры
        
        if if_detail_protokol_on_screen: content=content+'</body></html>'
        start_response('200 OK', [('Content-Type','text/html')])
        return [content.encode('utf-8')]
    except Exception as S:
        content=str(S)
        MainProtokol(content,'Ошибка')
        
        start_response('200 OK', [('Content-Type','text/html')])
        return [content.encode('utf-8')]
