# набор переменных чисто для откладки
if_detail_protokol_on_screen=False             # True - выводить детальный протокол на экран. ! html-файлы, предусмотренные процессом - не выводятся
if_detail_protokol_in_file=False                # True - писать детальный протокол в файл детального протокола, определенный в переменной detail_protokol_file

detail_protokol_file='log/log0.csv'            # полный путь и имя файла, в который будет сохраняться детальный протокол, если переменная if_detail_protokol_in_file=True
main_protokol_file='log/log.txt'               # полный путь и имя файла, в который будет сохраняться главный протокол
json_arch_file='log/json.txt'                  # файл, в который сохранять все json-строки, полученные от ТГ-бота

token='5981288740:AAFttcQs_JwuJZscjCcvfKuiZ7TDkOu7qpQ'

# параметры подключения к PostgeSQL
user_name="c58504_refboard_na4u_ru"            # параметр подключения к БД PostgreSQL :: имя пользователя
passwd="SaSkuFuqmosur86"                       # параметр подключения к БД PostgreSQL :: пароль
host_name="postgres.c58504.h2"                 # параметр подключения к БД PostgreSQL :: IP или URL адрес хоста
port_id="5432"                                 # параметр подключения к БД PostgreSQL :: порт подключения к БД
database_name="c58504_refboard_na4u_ru"        # параметр подключения к БД PostgreSQL :: имя БД

