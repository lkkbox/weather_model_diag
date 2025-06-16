#!/nwpr/gfs/com120/.conda/envs/rd/bin/python

from pytools import timetools as tt
from pytools import nctools as nct
from pytools import caltools as ct
from pytools.terminaltools import FlushPrinter as Fp
import numpy as np
import os

def main():
    modelName = 're_GEPSv3_CFSR'
    iMember = 0
    climDates = [tt.ymd2float(2001, 1, 1) + i for i in range(31)]
    climYears = [2001, 2020]
    NT = 64

    for climDate in climDates:
        run(modelName, iMember, climDate, climYears, NT)


def run(modelName, iMember, climDate, climYears, NT):
    def getSrcPath(varName, initDate):
        return tt.float2format(
            initDate,
            f'../../data/processed/{modelName}/%Y/%m/%dz%H/E{iMember:03d}/qbud-16d_{varName}.nc'
        )

    def getDesPath(varName, climDate):
        return tt.float2format(
            climDate,
            f'../../data/processed/{modelName}/clim/E{iMember:03d}/1day/{varName}/{varName}_%m%d_{climYears[0]}-{climYears[1]}.nc'
        )

    fp = Fp()
    __, month, day = tt.float2ymd(climDate)
    climDate_str = tt.float2format(climDate, '%m-%d %H')
    fp.flush(climDate_str)
    
    if all([
        os.path.exists(getDesPath(varName, climDate))
        for varName in ['uqx', 'vqy', 'wqp']
    ]):
        fp.print(f'desPath already exists - {climDate_str}')
        return

    #
    # ---- make sure all the srcs paths exist
    for year in range(climYears[0], climYears[1]+1):
        for varName in ['u', 'v', 'w', 'q']:
            initDate = tt.ymd2float(year, month, day)
            path = getSrcPath(varName, initDate)
            if not os.path.exists(path):
                fp.print(f'file not found: {path}')
                return

    #
    # ---- calculate year by year
    def read(varName, year):
        initDate = tt.ymd2float(year, month, day)
        data, dims = nct.ncreadByDimRange(
            getSrcPath(varName, initDate), varName, [
                [None]*2, [500_00, 1000_00], [-35, 35], [None]*2
            ],
        )
        # ---- padding Nan to the end
        if data.shape[0] < NT:
            dnt = NT - data.shape[0]
            data = np.concatenate(
                (data, np.nan * np.ones((dnt, *data.shape[1:]))),
                axis=0,
            )
        return data, dims
    
    
    for year in range(climYears[0], climYears[1]+1):
        fp.flush(f'{climDate_str} - reading {year}..')
        q, dims_q = read('q', year)

        # ---- cal constants and initialize output
        if year == climYears[0]:
            _, lev, lat, lon = dims_q
            dx, dy = ct.lonlat2dxdy(lon, lat)
            dlev = np.gradient(lev)

            uqx_sum = np.zeros_like(q)
            vqy_sum = np.zeros_like(q)
            wqp_sum = np.zeros_like(q)

            uqx_count = np.zeros_like(q)
            vqy_count = np.zeros_like(q)
            wqp_count = np.zeros_like(q)

        def readAndCheckDim(varName):
            data, dims = read(varName, year)
            if not all([all(dims[i]==dims_q[i]) for i in range(4)]):
                fp.print(f'{year=} {varName} dimension not equal')
                return None

            return data, dims
            
        u, dims = readAndCheckDim('u')
        if u is None: return
        v, dims = readAndCheckDim('v')
        if v is None: return
        w, dims = readAndCheckDim('w')
        if w is None: return

        def nanadd(data1, data2):
            mask = (~np.isnan(data1) & ~np.isnan(data2))
            sumdata = np.zeros_like(data1)
            sumdata[mask] = data1[mask] + data2[mask]
            return sumdata, mask

        uqx = u * np.gradient(q, axis=-1) / dx
        vqy = v * np.gradient(q, axis=-2) / dy
        wqp = w * np.gradient(q, axis=-3) / dlev[:, None, None]

        uqx_sum, uqx_mask = nanadd(uqx_sum, uqx)
        vqy_sum, vqy_mask = nanadd(vqy_sum, vqy)
        wqp_sum, wqp_mask = nanadd(wqp_sum, wqp)

        uqx_count += uqx_mask
        vqy_count += vqy_mask
        wqp_count += wqp_mask

    uqx_sum /= uqx_count
    vqy_sum /= vqy_count
    wqp_sum /= wqp_count

    #
    # ---- save output
    for varName, varData in zip(['uqx', 'vqy', 'wqp'], [uqx_sum, vqy_sum, wqp_sum]):
        fp.flush(f'{climDate_str} saving {varName}..')
        nct.save(
            getDesPath(varName, climDate), {
                varName: varData,
                'time': [climDate + lead for lead in dims[0]],
                'lev': lev,
                'lat': lat,
                'lon': lon,
            },
            overwrite=True,
        )

    fp.print(f'{climDate_str} finished!')


if __name__ == '__main__':
    main()
