class CoordinatesConverter(object):

  @staticmethod
  def ch1903ToWgs84(east: float, north: float):
    """
    --------------------------------------------------------------------------
    Reference: Solutions approchees pour la transformation de coordonnees
    CH1903-WGS84, Office federal de topographie swisstopo, Octobre 2005.
    --------------------------------------------------------------------------

    --------------------------------------------------------------------------
    A few precise points to check the algorithm:
    //
    Location        Easting     Northing    Height    Longitude (E)  Latitude (N)    Height
    -----------------------------------------------------------------------------------------
    Zimmerwald      602030.680  191775.030   897.915  7.46527319611  46.87709460056   947.149
    Chrischona      617306.300  268507.300   456.064  7.66860641028  47.56705147250   504.935
    Pfaender        776668.105  265372.681  1042.624  9.78436047861  47.51532577694  1089.372
    La Givrine      497313.292  145625.438  1207.434  6.10203510028  46.45408056139  1258.274
    Monte Generoso  722758.810   87649.670  1636.600  9.02121918139  45.92928833889  1685.027
    --------------------------------------------------------------------------
    """
    # Swiss grid limits.
    eastmax = 880000
    eastmin = 450000
    northmax = 330000
    northmin = 50000

    # Transform coordinates.
    hgt = 0
    
    # Convert origin to "civil" system, where Bern has coordinates 0.0.
    east -= 600000
    north -= 200000

    # Express distances in 1000km units.
    east /= 1E6
    north /= 1E6

    # Calculate longitude in 10000" units.
    lon = 2.6779094  
    lon += 4.728982 * east
    lon += 0.791484 * east * north
    lon += 0.1306 * east * north * north
    lon -= 0.0436 * east * east * east
    
    # Calculate latitude in 10000" units.
    lat = 16.9023892
    lat += 3.238272 * north
    lat -= 0.270978 * east * east
    lat -= 0.002528 * north * north
    lat -= 0.0447 * east * east * north
    lat -= 0.0140 * north * north * north
    
    # Convert height [m].
    # hgt += 49.55
    # hgt -= 12.60 * east
    # hgt -= 22.64 * north
    
    # Convert longitude and latitude back in degrees.
    lon *= 100 / 36
    lat *= 100 / 36

    return [lon, lat]
