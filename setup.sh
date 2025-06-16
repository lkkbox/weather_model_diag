git init
git pull https://github.com/lkkbox/weather_model_diag
root=$PWD

cd $root/analysis
ln -s /nwpr/gfs/com120/0_tools/pytools/ .

cd $root/analysis/modules/mjo/rmm/
ln -s ~/0_tools/MJO/RMM_WH04/rmmPhaseDiagram.py ~/0_tools/MJO/RMM_WH04/RMM_Tool.py .
