#!/bin/bash

mkdir -p output
./allot_new.py > output/big_output.log # change this file name if required

grep '^C9' output/big_output.log | cut -d"," -f2-4,8 | sort > output/course_wise.csv

grep '^S9' output/big_output.log | grep -v 'False' | cut -d"," -f2,4,5,7,8 | sed 's/^ //' | sort > output/student_wise.csv

grep '^S9' output/big_output.log | grep -v 'False' | cut -d"," -f2,4,5,7,8,9 | sed 's/^ //' | grep -e ' 1$' -e '0-ChoiceN' | cut -d"," -f1-5 | sort > output/first_choicers.csv

grep '^C7' output/big_output.log | cut -d"," -f2- > output/consolidated_closing_ranks.csv

grep '^C8' output/big_output.log | cut -d"," -f2- | sed 's/^ //' > output/unallotted.txt
grep '^C3' output/big_output.log | cut -d"," -f2- | sed 's/^ //' | grep -e '_pd_Y' > output/unallotted_in_pd.txt
grep '^C3' output/big_output.log | cut -d"," -f2- | sed 's/^ //' | grep 'B_pd_N' > output/unallotted_in_B.txt

grep 'Expanded by' output/big_output.log | cut -d" " -f2- > output/ties_found_in.txt

# grep '^S9' output/big_output.log | cut -d"," -f2-7 | sed 's/ //g' | grep -v 'False' | sed 's/-..,/,/' > output/allotment_for_complaint_check.csv

#./complaint_check.py > output/complaint_check_output.log

#grep '^Z' output/complaint_check_output.log > output/warnings_from_complaint_checks.log

#grep '^C4' big_output.log  | grep -e 'MS' -e 'MA' | grep '\<114\>' 

#tail -n15 output/complaint_check_output.log 

