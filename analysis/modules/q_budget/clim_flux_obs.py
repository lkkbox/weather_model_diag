#!/nwpr/gfs/com120/.conda/envs/rd/bin/python
from pytools import timetools as tt
from pytools import nctools as nct
from pytools import caltools as ct
from pytools.terminaltools import FlushPrinter as Fp
import numpy as np
import os

def main():
    for hour in [0, 6, 12, 18]:
        for iDay in range(31 + 15):
            run(iDay, hour)


def run(iDay, hour):
    fp = Fp()
    minMaxYear = [2001, 2020]
    __, month, day = tt.float2ymd(iDay)
    date = tt.ymd2float(2000, month, day, hour)
    date_str = tt.float2format(date, '%m-%d %H')
    fp.flush(date_str)
    
    #
    # ---- make sure all the srcs paths exist
    for year in range(minMaxYear[0], minMaxYear[1]+1):
        for varName in ['u', 'v', 'w', 'q']:
            date = tt.ymd2float(year, month, day, hour)
            path = getSrcPath(varName, date)
            if not os.path.exists(path):
                fp.print(f'file not found: {path}')
                return

    #
    # ---- calculate year by year
    def read(varName, year):
        date = tt.ymd2float(year, month, day, hour)
        return nct.ncreadByDimRange(
            getSrcPath(varName, date), varName, [[None]*2, [500, 1000], [-35, 35], [None]*2],
        )
    
    if all([
        os.path.exists(getDesPath(varName, date))
        for varName in ['uqx', 'vqy', 'wqp']
    ]):
        fp.print(f'desPath already exists - {date_str}')
        return

    
    for year in range(minMaxYear[0], minMaxYear[1]+1):
        fp.flush(f'{date_str} - reading {year}..')
        q, dims_q = read('q', year)

        #
        # ---- cal constants and initialize output
        if year == minMaxYear[0]:
            __, lev, lat, lon = dims_q
            dx, dy = ct.lonlat2dxdy(lon, lat)
            dlev = np.gradient(lev) * 100

            uqx_out = np.zeros_like(q)
            vqy_out = np.zeros_like(q)
            wqp_out = np.zeros_like(q)

        #
        # ---- u * dq/dx
        def readAndCheckDim(varName):
            data, dims = read(varName, year)
            if not all([all(dims[i]==dims_q[i]) for i in range(4)]):
                fp.print(f'{year=} {varName} dimension not equal')
                return None
            return data
            
        u = readAndCheckDim('u')
        if u is None:
            return
        uqx_out += u * np.gradient(q, axis=-1) / dx
        del(u)

        v = readAndCheckDim('v')
        if v is None:
            return
        vqy_out += v * np.gradient(q, axis=-2) / dy
        del(v)

        w = readAndCheckDim('w')
        if w is None:
            return
        wqp_out += w * np.gradient(q, axis=-3) / dlev[:, None, None]

    numYears = minMaxYear[1] - minMaxYear[0] + 1
    uqx_out /= numYears
    vqy_out /= numYears
    wqp_out /= numYears

    #
    # ---- save output
    for varName, varData in zip(['uqx', 'vqy', 'wqp'], [uqx_out, vqy_out, wqp_out]):
        fp.flush(f'{date_str} saving {varName}..')
        nct.save(
            getDesPath(varName, date), {
                varName: varData,
                'time': [date],
                'lev': lev,
                'lat': lat,
                'lon': lon,
            },
            overwrite=True,
        )

    fp.print(f'{date_str} finished!')

def getSrcPath(varName, date):
    return tt.float2format(
        date, f'./PRS/{varName.upper()}/%Y/ERA5_PRS_{varName.upper()}_%Y%m%d-%H%M.nc'
    )

def getDesPath(varName, date):
    return tt.float2format(
        date, f'./clim_6hr/{varName}/ERA5_PRS_{varName}_%m%d-%H%M.nc'
    )


if __name__ == '__main__':
    main()
