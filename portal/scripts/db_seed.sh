#!/bin/bash

export DJANGO_SUPERUSER_PASSWORD="123"

./manage.py createsuperuser --no-input \
  --username admin \
  --email admin@lisbondatascience.org

./manage.py create-instructor \
  -u "catarina" \
  -p "catarina1234" \
  -e "catarina@lisbondatascience.org" \
  -n "Catarina" \
  -git "Catarina" \
  -s "U21392CAT" \
  -g "female" \
  -t "regular" \

./manage.py create-instructor \
  -u "ines" \
  -p "ines1234" \
  -e "ines@lisbondatascience.org" \
  -n "Ines" \
  -git "Ines" \
  -s "U21392INES" \
  -g "female" \
  -t "regular" \

./manage.py create-instructor \
  -u "hugo" \
  -p "hugo1234" \
  -e "hugo@lisbondatascience.org" \
  -n "Hugo" \
  -git "Hugo" \
  -s "U21392HUGO" \
  -g "male" \
  -t "regular" \

./manage.py create-student \
  -u "ana.silva" \
  -p "ana1234" \
  -e "anasilva@lisbondatascience.org" \
  -n "Ana Silva" \
  -git "AnaSilva" \
  -s "U21392ANA" \
  -g "female" \
  -t "regular" \

./manage.py create-student \
  -u "joao.silva" \
  -p "joao1234" \
  -e "joaosilva@lisbondatascience.org" \
  -n "João Silva" \
  -git "JoaoSilva" \
  -s "U21392JOAO" \
  -g "male" \
  -t "regular" \

./manage.py create-student \
  -u "pedro.silva" \
  -p "pedro1234" \
  -e "pedrosilva@lisbondatascience.org" \
  -n "Pedro Silva" \
  -git "PedroSilva" \
  -s "U21392PEDRO" \
  -g "male" \
  -t "regular" \

./manage.py create-student \
  -u "joana.silva" \
  -p "joana1234" \
  -e "joanasilva@lisbondatascience.org" \
  -n "Joana Silva" \
  -git "JoanaSilva" \
  -s "U21392JOANA" \
  -g "female" \
  -t "regular" \

./manage.py create-spec \
  -c "S01" \
  -n "Bootcamp"

duedate=`date "+%Y-%m-%d" -d "+30 days"`

for i in {1..20}
do
	./manage.py create-unit \
  -s "S01" \
  -c "SLU0${i}" \
  -n "SLU0${i} - test unit ${i}" \
  -i "catarina" \
  -due $duedate
done

./manage.py create-spec \
  -c "S02" \
  -n "Test Specialization"

for i in {1..3}
do
	./manage.py create-unit \
  -s "S02" \
  -c "BLU0${i}" \
  -n "BLU0${i} - test unit ${i}" \
  -i "catarina" \
  -due $duedate
done
