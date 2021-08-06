#!/bin/bash
NB_TRY=10
PAUSE=5
PROJECT="wikifundi"

function running_status
{
  RUNNING=0;

  for i in `sloppy show -r  $PROJECT | jq .[0].apps[].status[0]`
  do
    if [ !  "$i" = "\"running\""  ]
    then
      RUNNING=1 ;
    fi
  done
}

function wait_running
{
  RUNNING=1;
  while [ $RUNNING -eq 1 ]
  do
    echo "in process ..."
    running_status
    sleep $PAUSE
  done
  echo "all instances running !"
}

function get_list_apps
{
  APPS=`sloppy show -r  $PROJECT | jq .[0].apps[].id | cut -d \" -f 2`
}

function restart_app
{
  echo "restart $app"
  sloppy restart $PROJECT/$PROJECT/$app
}

function delete_app
{
  echo "delete $app"
  sloppy delete $PROJECT/$PROJECT/$app
}

function restart_all
{
  get_list_apps

  for app in $APPS
  do
    restart_app
    sleep $PAUSE
  done
}

function get_app_from_lang
{
  lang=$1
  app="wikifundi-$lang"
}

function restart
{
  lang=$1
  if [ -z $lang ]
  then
    restart_all
  else
    get_app_from_lang $lang
    restart_app
  fi
}


function sloppy_change
{
  PARAMS=$1
  sloppy change $PARAMS
}

function delete_all
{
  if [ "$1" == "force" ]
  then
    rep="delete_all"
  else
    echo "type delete_all to confirm"
    read rep
  fi
  if [ $rep == "delete_all" ]
  then
    get_list_apps

    for app in $APPS
    do
      delete_app
      sleep $PAUSE
    done
  fi
}

function partial_mirroring
{
  sloppy_change sloppy-partial-mirroring.json

  wait_running

  restart_all
}

function full_mirroring
{
  for i in `seq 1 $NB_TRY`
  do
    echo "Try to reset all #$i"

    delete_all "force"

    sleep $PAUSE
    sleep $PAUSE
    sleep $PAUSE
    sleep $PAUSE

    if sloppy_change sloppy-full-mirroring.json
    then
      return
    fi
  done
}

function cron
{
  #run full mirroring only the sunday
  if [ `date +%w` == "0" ]
  then
    full_mirroring
  else
    partial_mirroring
  fi
}

ACTION=$1

case $ACTION in
  restart)
    restart $2
    ;;
  full_mirroring)
    full_mirroring
    ;;
  partial_mirroring)
    partial_mirroring
    ;;
  wait_running)
    wait_running
    ;;
  delete_all)
    delete_all $2
    ;;
  cron)
    cron
    ;;
esac



