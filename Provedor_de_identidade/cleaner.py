#!/usr/bin/python

##mysql
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="registration",
  password="senha",
  database="registration"
);

cur = mydb.cursor();

from datetime import datetime, timedelta

cinco_minutos_atras = datetime.now() - timedelta(minutes=5);

cur.execute(f"delete from temp_token where hour < '{cinco_minutos_atras}'");
cur.execute("commit;");
