# rcgrouper
Script to get postings from RCGroups.com Classifieds matching user-defined keywords

## Instructions:
1. Update `example.grouper` with the necessary information and change the filename to `.grouper`.
2. Add the script as a cron job if you want. EX:

    $ crontab -e

    ...
    # and in the crontab file:
    * * * * * /path/to/rcgrouper.py

This will set the script to run once a minute. However, not that you will only be sent postings if they are new (i.e., if you have not been sent them before).
