non_vulnerability_fixing_commit_example=$(head -n 1 ../dataset/VFD/all_non_vul_fix.txt)
vulnerability_fixing_commit_example=$(head -n 1 ../dataset/VFD/all_vul_fix.txt)

touch path.txt
echo $non_vulnerability_fixing_commit_example > path.txt
echo $vulnerability_fixing_commit_example >> path.txt

python vul_fix_check.py --llm deepseek-coder-v2:236b