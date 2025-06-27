#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import pytools as pyt
import os


def main():
    caseDate = pyt.tt.ymd2float(2009, 1, 26)
    numDates = 5
    area = [100, 180, -15, 15]
    levelTop = 700
    overwrite = True

    # ---- check write permission and if the output already exists
    desDirRoot = '/nwpr/gfs/com120/6_weatherModelDiag/data/q_budget/obs'
    if not os.path.exists(desDirRoot):
        raise FileNotFoundError(f'{desDirRoot=}')

    desSubDir = pyt.tt.float2format(caseDate, '%y%m%d')
    desDir = f'{desDirRoot}/{desSubDir}'
    desBaseName = f'a{'_'.join([str(a) for a in area])}_l{levelTop}_d{numDates}.nc'
    desPath = f'{desDir}/{desBaseName}'

    if os.path.exists(desPath) and not overwrite:
        print(f'desPath already exists and overwrite=False. {desPath=}')
        return

    if not os.path.exists(desDir):
        os.makedirs(desDir)

    # ---- begins -- read data
    minMaxTime = [caseDate, caseDate + numDates - 0.01]
    minMaxs = [minMaxTime, [levelTop, 1000], area[2:], area[:2]]
    # u = readTotal('u', minMaxs)
    # v = readTotal('v', minMaxs)
    # w = readTotal('w', minMaxs)
    # q = readTotal('q', minMaxs)






def readTotal(varName, minMaxs):
    fp = pyt.tmt.FlushPrinter()
    fp.flush(f'reading total {varName}.. ')
    data, dims = pyt.rt.obsReader.total(varName, minMaxs, source='era5_prs_6hr')
    return data, dims


if __name__ == '__main__':
    main()
