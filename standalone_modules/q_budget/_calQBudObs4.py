#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
import shared as st
import pytools.terminaltools as tmt
import pytools.timetools as tt
import pytools.filetools as ft
import os


def main():
    caseDates = [
        tt.format2float(d, '%Y%m%d') for d in [
            '20010125', '20020124', '20030130', '20040128', '20050105', '20060112',
            '20080129', '20090126', '20120129', '20160114', '20180119', '20190120',
            '20240106',
        ]
    ]
    for caseDate in caseDates:
        run(caseDate)

def run(caseDate):
    #
    # ---- settings
    area = [120, 180, -5, 5]
    area = [120, 170, -13, 3]
    minMaxLevels = [700, 1000]
    deltaDates = [-35, 15+35]

    #
    # ---- don't touch
    fp = tmt.FlushPrinter()
    outPath = tt.float2format(
        caseDate,
        f'./data/cal/{ft.getPyName()}_%Y%m%d_{'_'.join([str(i) for i in [*area, *minMaxLevels]])}.nc'
    )

    if os.path.exists(outPath):
        print(f'file already exists: {outPath}')
        return
    
    print(outPath)

    #
    # ---- read data
    minMaxsRead = [
        [caseDate + s + d for s, d in zip(deltaDates, [0, 0.99])],
        [l*100 for l in minMaxLevels],
        [s + d for s, d in zip(area[2:], [-3, 3])],
        [s + d for s, d in zip(area[:2], [-3, 0])],
    ]  # +/- 3 deg for interolation/gradient

    fp.flush('reading..')
    sp, __ = st.readObs('sp', caseDate, minMaxsRead)
    u, dims = st.readObs('u', caseDate, minMaxsRead)
    v, dims = st.readObs('v', caseDate, minMaxsRead)
    w, dims = st.readObs('w', caseDate, minMaxsRead)
    q, dims = st.readObs('q', caseDate, minMaxsRead)

    #
    # ---- cal and save
    st.calSaveBud4(
        sp, u, v, w, q, dims,
        minMaxLevels, area,
        fp, outPath,
    )


if __name__ == '__main__':
    main()
