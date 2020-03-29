#!/bin/bash
for i in $(ls -l | awk '{print $9}') ; do 
 cat ${i} | cut -d, -f1 > ../lists/${i} 
done
