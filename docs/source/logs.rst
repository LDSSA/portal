Logs
========

How to check the logs of student submissions.

#. find a grade that you want to inspect
    * https://portal.lisbondatascience.org/4c7Kbkny9iMCmxxULdOKZk0Ld4WBLVtW/academy/grade/4667/change/
    * .. image :: assets/1.png

#. go to aws 
    * https://ldsa.signin.aws.amazon.com/console
    * .. image :: assets/2.png
    
#. in the cloudwatch logs in the application log group search for logs with that students username (if it has dots and such it might not be a direct match)
    * https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#
    * .. image :: assets/3.png

#. those are the logs for the container that ran the grading, it will probably have some clues to what happened
    * .. image :: assets/3.png
