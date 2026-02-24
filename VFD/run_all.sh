non_vulnerability_fixing_commits=$(cat ../dataset/VFD/all_non_vul_fix.txt)
vulnerability_fixing_commits=$(cat ../dataset/VFD/all_vul_fix.txt)

touch path.txt
echo $non_vulnerability_fixing_commits > path.txt
echo $vulnerability_fixing_commits >> path.txt

python vul_fix_check.py --llm deepseek-coder-v2:236b