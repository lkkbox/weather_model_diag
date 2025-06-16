root=$PWD

cd $root/analysis
rm pytools
ln -s /nwpr/gfs/com120/0_tools/pytools/ .


cd $root/analysis/modules/mjo/rmm/
rm rmmPhaseDiagram.py RMM_Tool.py
ln -s ~/0_tools/MJO/RMM_WH04/rmmPhaseDiagram.py ~/0_tools/MJO/RMM_WH04/RMM_Tool.py .

