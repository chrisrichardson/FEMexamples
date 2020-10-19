# Copyright 2017 Chris Richardson (chris@bpi.cam.ac.uk)
""" A super simple library for low volume two-dimensional unstructured meshes.
    Meshes are stored as python dicts containing 'geometry', 'topology',
    'data', and can be read from a URL pointing to a text-based XDMF file """

import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy

def get(url):
    """ Read a mesh in XDMF XML format (not HDF5) from a URL"""
    try:
        import requests
        import xml.etree.ElementTree as ET
    except ImportError:
        raise("Missing required library")

    r = requests.get(url)
    if r.status_code != 200:
        raise IOError("Cannot read from URL")

    et = ET.fromstring(r.text)
    assert(et.tag == 'Xdmf')
    assert(et[0].tag == 'Domain')
    assert(et[0][0].tag == 'Grid')
    grid = et[0][0]

    # Get topology array
    topology = grid.find('Topology')
    assert(topology.attrib['TopologyType'] == 'Triangle')
    tdims = numpy.fromstring(topology[0].attrib['Dimensions'], sep=' ', dtype='int')
    nptopo = numpy.fromstring(topology[0].text, sep=' ', dtype='int').reshape(tdims)

    # Get geometry array
    geometry = grid.find('Geometry')
    assert(geometry.attrib['GeometryType'] == 'XY')
    gdims = numpy.fromstring(geometry[0].attrib['Dimensions'], sep=' ', dtype='int')
    npgeom = numpy.fromstring(geometry[0].text, sep=' ', dtype='float').reshape(gdims)

    # Find all attributes and put them in a list
    attrlist = grid.findall('Attribute')
    data_all = []
    for attr in attrlist:
        adims = numpy.fromstring(attr[0].attrib['Dimensions'], sep=' ', dtype='int')
        npattr = attr.attrib
        npattr['value'] = numpy.fromstring(attr[0].text, sep=' ', dtype='int')
        data_all.append(npattr)

    mesh = {'geometry':npgeom, 'topology':nptopo, 'data':data_all}

    return mesh

def rectangle_mesh(nx, ny):
    """Make a rectangular mesh of triangles, nx by ny."""
    assert(isinstance(nx, int))
    assert(isinstance(ny, int))
    c = 0
    geometry = zeros((nx*ny, 2), dtype='float')
    for i in range(nx):
        for j in range(ny):
            geometry[c] = [float(i/(nx-1)), float(j/(ny-1))]
            c += 1

    ntri = (nx - 1)*(ny - 1)*2
    topology = zeros((ntri, 3), dtype='int')

    c = 0
    for i in range(nx - 1):
        for j in range(ny - 1):
            ij = j + i*ny
            topology[c] = [ij, ij+ny, ij+ny+1]
            topology[c + 1] = [ij+1, ij, ij+ny+1]
            c += 2

    mesh = {'geometry':geometry, 'topology':topology}
    return mesh

def plot(mesh, *args, **kwargs):
    """ Plot a mesh with matplotlib, possibly with associated data,
        which may be associated with points or triangles """

    # FIXME: check keys of mesh contain geometry and topology
    geom, topo = mesh['geometry'], mesh['topology']
    x = geom[:,0]
    y = geom[:,1]

    plt.gca(aspect='equal')

    if args:
        data = args[0]
        if len(data)==len(geom):
            plt.tricontourf(x, y, topo, data, 40, **kwargs)
        elif len(data)==len(topo):
            tr = tri.Triangulation(x, y, topo)
            plt.tripcolor(tr, data, **kwargs)
        else:
            raise RuntimeError("Data is wrong length")

    plt.triplot(x, y, topo, color='k', alpha=0.5)

    xmax = x.max()
    xmin = x.min()
    ymax = y.max()
    ymin = y.min()
    dx = 0.1*(xmax - xmin)
    dy = 0.1*(ymax - ymin)
    plt.xlim(xmin-dx, xmax+dx)
    plt.ylim(ymin-dy, ymax+dy)

    return
