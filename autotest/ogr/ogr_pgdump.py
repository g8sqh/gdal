#!/usr/bin/env pytest
###############################################################################
# $Id$
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test read functionality for OGR PGDump driver.
# Author:   Even Rouault <even dot rouault at spatialys.com>
#
###############################################################################
# Copyright (c) 2010-2013, Even Rouault <even dot rouault at spatialys.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

import os

import gdaltest
import ogrtest
import pytest

from osgeo import gdal, ogr, osr

###############################################################################
# Create table from data/poly.shp


def test_ogr_pgdump_1():

    try:
        os.remove("tmp/tpoly.sql")
    except OSError:
        pass

    ds = ogr.GetDriverByName("PGDump").CreateDataSource("tmp/tpoly.sql")

    ######################################################
    # Create Layer
    lyr = ds.CreateLayer("tpoly", options=["DIM=3", "POSTGIS_VERSION=1.5"])

    ######################################################
    # Setup Schema
    ogrtest.quick_create_layer_def(
        lyr,
        [
            ("AREA", ogr.OFTReal),
            ("EAS_ID", ogr.OFTInteger),
            ("PRFEDEA", ogr.OFTString),
            ("SHORTNAME", ogr.OFTString, 8),
        ],
    )

    ######################################################
    # Copy in poly.shp

    dst_feat = ogr.Feature(feature_def=lyr.GetLayerDefn())

    shp_ds = ogr.Open("data/poly.shp")
    shp_lyr = shp_ds.GetLayer(0)
    feat = shp_lyr.GetNextFeature()
    gdaltest.poly_feat = []

    while feat is not None:

        gdaltest.poly_feat.append(feat)

        dst_feat.SetFrom(feat)
        lyr.CreateFeature(dst_feat)

        feat = shp_lyr.GetNextFeature()

    dst_feat.Destroy()
    ds.Destroy()

    f = open("tmp/tpoly.sql")
    sql = f.read()
    f.close()

    assert not (
        sql.find("""DROP TABLE IF EXISTS "public"."tpoly" CASCADE;""") == -1
        or sql.find(
            """DELETE FROM geometry_columns WHERE f_table_name = 'tpoly' AND f_table_schema = 'public';"""
        )
        == -1
        or sql.find("""BEGIN;""") == -1
        or sql.find(
            """CREATE TABLE "public"."tpoly" ( "ogc_fid" SERIAL, CONSTRAINT "tpoly_pk" PRIMARY KEY ("ogc_fid") );"""
        )
        == -1
        or sql.find(
            """SELECT AddGeometryColumn('public','tpoly','wkb_geometry',-1,'GEOMETRY',3);"""
        )
        == -1
        or sql.find(
            """CREATE INDEX "tpoly_wkb_geometry_geom_idx" ON "public"."tpoly" USING GIST ("wkb_geometry");"""
        )
        == -1
        or sql.find("""ALTER TABLE "public"."tpoly" ADD COLUMN "area" FLOAT8;""") == -1
        or sql.find("""ALTER TABLE "public"."tpoly" ADD COLUMN "eas_id" INTEGER;""")
        == -1
        or sql.find("""ALTER TABLE "public"."tpoly" ADD COLUMN "prfedea" VARCHAR;""")
        == -1
        or sql.find(
            """ALTER TABLE "public"."tpoly" ADD COLUMN "shortname" VARCHAR(8);"""
        )
        == -1
        or sql.find(
            """INSERT INTO "public"."tpoly" ("wkb_geometry" , "area", "eas_id", "prfedea") VALUES ('01030000800100000005000000000000C01A481D4100000080072D5241000000000000000000000060AA461D4100000080FF2C524100000000000000000000006060461D41000000400C2D52410000000000000000000000A0DF471D4100000000142D52410000000000000000000000C01A481D4100000080072D52410000000000000000', 5268.813, 170, '35043413');"""
        )
        == -1
        or sql.find("""COMMIT;""") == -1
    )


###############################################################################
# Create table from data/poly.shp with PG_USE_COPY=YES


def test_ogr_pgdump_2():

    try:
        os.remove("tmp/tpoly.sql")
    except OSError:
        pass

    gdal.SetConfigOption("PG_USE_COPY", "YES")

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "tmp/tpoly.sql", options=["LINEFORMAT=CRLF"]
    )

    ######################################################
    # Create Layer
    lyr = ds.CreateLayer(
        "tpoly",
        geom_type=ogr.wkbPolygon,
        options=["SCHEMA=another_schema", "SRID=4326", "GEOMETRY_NAME=the_geom"],
    )

    ######################################################
    # Setup Schema
    ogrtest.quick_create_layer_def(
        lyr,
        [
            ("AREA", ogr.OFTReal),
            ("EAS_ID", ogr.OFTInteger),
            ("PRFEDEA", ogr.OFTString),
            ("SHORTNAME", ogr.OFTString, 8),
        ],
    )

    ######################################################
    # Copy in poly.shp

    dst_feat = ogr.Feature(feature_def=lyr.GetLayerDefn())

    shp_ds = ogr.Open("data/poly.shp")
    shp_lyr = shp_ds.GetLayer(0)
    feat = shp_lyr.GetNextFeature()
    gdaltest.poly_feat = []

    while feat is not None:

        gdaltest.poly_feat.append(feat)

        dst_feat.SetFrom(feat)
        lyr.CreateFeature(dst_feat)

        feat = shp_lyr.GetNextFeature()

    dst_feat.Destroy()
    ds.Destroy()

    gdal.SetConfigOption("PG_USE_COPY", "NO")

    f = open("tmp/tpoly.sql")
    sql = f.read()
    f.close()

    assert not (
        sql.find("""DROP TABLE IF EXISTS "another_schema"."tpoly" CASCADE;""") == -1
        or sql.find("""BEGIN;""") == -1
        or sql.find(
            """CREATE TABLE "another_schema"."tpoly" ( "ogc_fid" SERIAL, CONSTRAINT "tpoly_pk" PRIMARY KEY ("ogc_fid") );"""
        )
        == -1
        or sql.find(
            """SELECT AddGeometryColumn('another_schema','tpoly','the_geom',4326,'POLYGON',2);"""
        )
        == -1
        or sql.find(
            """CREATE INDEX "tpoly_the_geom_geom_idx" ON "another_schema"."tpoly" USING GIST ("the_geom");"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "area" FLOAT8;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "eas_id" INTEGER;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "prfedea" VARCHAR;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "shortname" VARCHAR(8);"""
        )
        == -1
        or sql.find(
            """COPY "another_schema"."tpoly" ("the_geom", "area", "eas_id", "prfedea", "shortname") FROM STDIN;"""
        )
        == -1
        or sql.find(
            "0103000020E61000000100000005000000000000C01A481D4100000080072D524100000060AA461D4100000080FF2C52410000006060461D41000000400C2D5241000000A0DF471D4100000000142D5241000000C01A481D4100000080072D5241	5268.813	170	35043413	\\N"
        )
        == -1
        or sql.find(r"""\.""") == -1
        or sql.find("""COMMIT;""") == -1
    )


###############################################################################
# Create table from data/poly.shp without any geometry


def test_ogr_pgdump_3():

    try:
        os.remove("tmp/tpoly.sql")
    except OSError:
        pass

    gdal.SetConfigOption("PG_USE_COPY", "YES")

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "tmp/tpoly.sql", options=["LINEFORMAT=LF"]
    )

    ######################################################
    # Create Layer
    lyr = ds.CreateLayer(
        "tpoly", geom_type=ogr.wkbNone, options=["SCHEMA=another_schema"]
    )

    ######################################################
    # Setup Schema
    ogrtest.quick_create_layer_def(
        lyr,
        [
            ("EMPTYCHAR", ogr.OFTString),
            ("AREA", ogr.OFTReal),
            ("EAS_ID", ogr.OFTInteger),
            ("PRFEDEA", ogr.OFTString),
            ("SHORTNAME", ogr.OFTString, 8),
        ],
    )

    ######################################################
    # Copy in poly.shp

    dst_feat = ogr.Feature(feature_def=lyr.GetLayerDefn())

    shp_ds = ogr.Open("data/poly.shp")
    shp_lyr = shp_ds.GetLayer(0)
    feat = shp_lyr.GetNextFeature()
    gdaltest.poly_feat = []

    i = 0

    while feat is not None:

        gdaltest.poly_feat.append(feat)

        dst_feat.SetFrom(feat)
        if i == 0:
            # Be perverse and test the case where a feature has a geometry
            # even if it's a wkbNone layer ! (#4040)
            dst_feat.SetGeometry(ogr.CreateGeometryFromWkt("POINT(0 1)"))
        elif i == 1:
            # Field with 0 character (not empty!) (#4040)
            dst_feat.SetField(0, "")
        i = i + 1
        lyr.CreateFeature(dst_feat)

        feat = shp_lyr.GetNextFeature()

    dst_feat.Destroy()
    ds.Destroy()

    gdal.SetConfigOption("PG_USE_COPY", "NO")

    f = open("tmp/tpoly.sql")
    sql = f.read()
    f.close()

    assert not (
        sql.find("""DROP TABLE IF EXISTS "another_schema"."tpoly" CASCADE;""") == -1
        or sql.find("""DELETE FROM geometry_columns""") != -1
        or sql.find("""BEGIN;""") == -1
        or sql.find(
            """CREATE TABLE "another_schema"."tpoly" (    "ogc_fid" SERIAL,    CONSTRAINT "tpoly_pk" PRIMARY KEY ("ogc_fid") );"""
        )
        == -1
        or sql.find("""SELECT AddGeometryColumn""") != -1
        or sql.find("""CREATE INDEX "tpoly_wkb_geometry_geom_idx""") != -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "area" FLOAT8;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "eas_id" INTEGER;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "prfedea" VARCHAR;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "another_schema"."tpoly" ADD COLUMN "shortname" VARCHAR(8);"""
        )
        == -1
        or sql.find(
            """COPY "another_schema"."tpoly" ("emptychar", "area", "eas_id", "prfedea", "shortname") FROM STDIN;"""
        )
        == -1
        or sql.find("""\\N	215229.266	168	35043411	\\N""") == -1
        or sql.find("""	5268.813	170	35043413	\\N""") == -1
        or sql.find("""\\.""") == -1
        or sql.find("""COMMIT;""") == -1
    )


###############################################################################
# Test multi-geometry support


def test_ogr_pgdump_4():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "tmp/ogr_pgdump_4.sql", options=["LINEFORMAT=LF"]
    )
    assert ds.TestCapability(ogr.ODsCCreateGeomFieldAfterCreateLayer) != 0

    ######################################################
    # Create Layer
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone, options=["WRITE_EWKT_GEOM=YES"])
    assert lyr.TestCapability(ogr.OLCCreateGeomField) != 0

    gfld_defn = ogr.GeomFieldDefn("point_nosrs", ogr.wkbPoint)
    lyr.CreateGeomField(gfld_defn)

    gfld_defn = ogr.GeomFieldDefn("poly", ogr.wkbPolygon25D)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    gfld_defn.SetSpatialRef(srs)
    lyr.CreateGeomField(gfld_defn)

    feat = ogr.Feature(lyr.GetLayerDefn())
    lyr.CreateFeature(feat)

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetGeomFieldDirectly("point_nosrs", ogr.CreateGeometryFromWkt("POINT (1 2)"))
    feat.SetGeomFieldDirectly(
        "poly",
        ogr.CreateGeometryFromWkt("POLYGON Z ((0 0 0,0 1 0,1 1 0,1 0 0, 0 0 0))"),
    )
    lyr.CreateFeature(feat)

    ds = None

    f = open("tmp/ogr_pgdump_4.sql")
    sql = f.read()
    f.close()

    assert not (
        sql.find(
            """CREATE TABLE "public"."test" (    "ogc_fid" SERIAL,    CONSTRAINT "test_pk" PRIMARY KEY ("ogc_fid") )"""
        )
        == -1
        or sql.find(
            """SELECT AddGeometryColumn('public','test','point_nosrs',0,'POINT',2)"""
        )
        == -1
        or sql.find(
            """CREATE INDEX "test_point_nosrs_geom_idx" ON "public"."test" USING GIST ("point_nosrs")"""
        )
        == -1
        or sql.find(
            """SELECT AddGeometryColumn('public','test','poly',4326,'POLYGON',3)"""
        )
        == -1
        or sql.find(
            """CREATE INDEX "test_poly_geom_idx" ON "public"."test" USING GIST ("poly")"""
        )
        == -1
        or sql.find("""INSERT INTO "public"."test" DEFAULT VALUES""") == -1
        or sql.find(
            """INSERT INTO "public"."test" ("point_nosrs" , "poly" ) VALUES (GeomFromEWKT('SRID=0;POINT (1 2)'::TEXT) , GeomFromEWKT('SRID=4326;POLYGON Z ((0 0 0,0 1 0,1 1 0,1 0 0,0 0 0))'::TEXT) )"""
        )
        == -1
    )


###############################################################################
# Test non nullable and unique field support


def test_ogr_pgdump_5():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_5.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone)
    field_defn = ogr.FieldDefn("field_not_nullable", ogr.OFTString)
    field_defn.SetNullable(0)
    lyr.CreateField(field_defn)
    field_defn = ogr.FieldDefn("field_nullable", ogr.OFTString)
    field_defn.SetUnique(True)
    lyr.CreateField(field_defn)
    field_defn = ogr.GeomFieldDefn("geomfield_not_nullable", ogr.wkbPoint)
    field_defn.SetNullable(0)
    lyr.CreateGeomField(field_defn)
    field_defn = ogr.GeomFieldDefn("geomfield_nullable", ogr.wkbPoint)
    lyr.CreateGeomField(field_defn)
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetField("field_not_nullable", "not_null")
    f.SetGeomFieldDirectly(
        "geomfield_not_nullable", ogr.CreateGeometryFromWkt("POINT(0 0)")
    )
    lyr.CreateFeature(f)
    f = None

    # Error case: missing geometry
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetField("field_not_nullable", "not_null")
    gdal.PushErrorHandler()
    ret = lyr.CreateFeature(f)
    gdal.PopErrorHandler()
    assert ret != 0
    f = None

    # Error case: missing non-nullable field
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetGeometryDirectly(ogr.CreateGeometryFromWkt("POINT(0 0)"))
    gdal.PushErrorHandler()
    ret = lyr.CreateFeature(f)
    gdal.PopErrorHandler()
    assert ret != 0
    f = None

    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_5.sql", "rb")
    sql = gdal.VSIFReadL(1, 1000, f).decode("ascii")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_5.sql")

    assert not (
        sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_not_nullable" VARCHAR NOT NULL;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_nullable" VARCHAR UNIQUE;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "test" ALTER COLUMN "geomfield_not_nullable" SET NOT NULL;"""
        )
        == -1
    )


###############################################################################
# Test default values


def test_ogr_pgdump_6():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_6.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone)

    field_defn = ogr.FieldDefn("field_string", ogr.OFTString)
    field_defn.SetDefault("'a''b'")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_int", ogr.OFTInteger)
    field_defn.SetDefault("123")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_real", ogr.OFTReal)
    field_defn.SetDefault("1.23")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_nodefault", ogr.OFTInteger)
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_datetime", ogr.OFTDateTime)
    field_defn.SetDefault("CURRENT_TIMESTAMP")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_datetime2", ogr.OFTDateTime)
    field_defn.SetDefault("'2015/06/30 12:34:56'")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_date", ogr.OFTDate)
    field_defn.SetDefault("CURRENT_DATE")
    lyr.CreateField(field_defn)

    field_defn = ogr.FieldDefn("field_time", ogr.OFTTime)
    field_defn.SetDefault("CURRENT_TIME")
    lyr.CreateField(field_defn)

    gdal.SetConfigOption("PG_USE_COPY", "YES")

    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetField("field_string", "a")
    f.SetField("field_int", 456)
    f.SetField("field_real", 4.56)
    f.SetField("field_datetime", "2015/06/30 12:34:56")
    f.SetField("field_datetime2", "2015/06/30 12:34:56")
    f.SetField("field_date", "2015/06/30")
    f.SetField("field_time", "12:34:56")
    lyr.CreateFeature(f)
    f = None

    # Transition from COPY to INSERT
    f = ogr.Feature(lyr.GetLayerDefn())
    lyr.CreateFeature(f)
    f = None

    # Transition from INSERT to COPY
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetField("field_string", "b")
    f.SetField("field_int", 456)
    f.SetField("field_real", 4.56)
    f.SetField("field_datetime", "2015/06/30 12:34:56")
    f.SetField("field_datetime2", "2015/06/30 12:34:56")
    f.SetField("field_date", "2015/06/30")
    f.SetField("field_time", "12:34:56")
    lyr.CreateFeature(f)
    f = None

    gdal.SetConfigOption("PG_USE_COPY", None)

    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_6.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("ascii")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_6.sql")

    assert not (
        """a\t456\t4.56\t\\N\t2015/06/30 12:34:56\t2015/06/30 12:34:56\t2015/06/30\t12:34:56"""
        not in sql
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_string" VARCHAR DEFAULT 'a''b';"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_int" INTEGER DEFAULT 123;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_real" FLOAT8 DEFAULT 1.23;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_datetime" timestamp with time zone DEFAULT CURRENT_TIMESTAMP;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_datetime2" timestamp with time zone DEFAULT '2015/06/30 12:34:56+00'::timestamp with time zone;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_date" date DEFAULT CURRENT_DATE;"""
        )
        == -1
        or sql.find(
            """ALTER TABLE "public"."test" ADD COLUMN "field_time" time DEFAULT CURRENT_TIME;"""
        )
        == -1
        or """b\t456\t4.56\t\\N\t2015/06/30 12:34:56\t2015/06/30 12:34:56\t2015/06/30\t12:34:56"""
        not in sql
    )


###############################################################################
# Test creating a field with the fid name (PG_USE_COPY=NO)


def test_ogr_pgdump_7():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_7.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone, options=["FID=myfid"])

    lyr.CreateField(ogr.FieldDefn("str", ogr.OFTString))
    gdal.PushErrorHandler()
    ret = lyr.CreateField(ogr.FieldDefn("myfid", ogr.OFTString))
    gdal.PopErrorHandler()
    assert ret != 0

    ret = lyr.CreateField(ogr.FieldDefn("myfid", ogr.OFTInteger))
    assert ret == 0
    lyr.CreateField(ogr.FieldDefn("str2", ogr.OFTString))

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "first string")
    feat.SetField("myfid", 10)
    feat.SetField("str2", "second string")
    ret = lyr.CreateFeature(feat)
    assert ret == 0
    assert feat.GetFID() == 10

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str2", "second string")
    ret = lyr.CreateFeature(feat)
    assert ret == 0
    if feat.GetFID() < 0:
        feat.DumpReadable()
        pytest.fail()
    if feat.GetField("myfid") != feat.GetFID():
        feat.DumpReadable()
        pytest.fail()

    # feat.SetField('str', 'foo')
    # ret = lyr.SetFeature(feat)
    # if ret != 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetFID(1)
    feat.SetField("myfid", 10)
    gdal.PushErrorHandler()
    ret = lyr.CreateFeature(feat)
    gdal.PopErrorHandler()
    assert ret != 0

    # gdal.PushErrorHandler()
    # ret = lyr.SetFeature(feat)
    # gdal.PopErrorHandler()
    # if ret == 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    # feat.UnsetField('myfid')
    # gdal.PushErrorHandler()
    # ret = lyr.SetFeature(feat)
    # gdal.PopErrorHandler()
    # if ret == 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "first string")
    feat.SetField("myfid", 12)
    feat.SetField("str2", "second string")
    ret = lyr.CreateFeature(feat)
    assert ret == 0
    assert feat.GetFID() == 12

    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_7.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("ascii")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_7.sql")

    assert not (
        """CREATE TABLE "public"."test" (    "myfid" SERIAL,    CONSTRAINT "test_pk" PRIMARY KEY ("myfid") )"""
        not in sql
        or """ALTER TABLE "public"."test" ADD COLUMN "myfid" """ in sql
        or sql.find(
            """INSERT INTO "public"."test" ("myfid" , "str", "str2") VALUES (10, 'first string', 'second string');"""
        )
        == -1
        or sql.find(
            """INSERT INTO "public"."test" ("str2") VALUES ('second string');"""
        )
        == -1
        or sql.find(
            """INSERT INTO "public"."test" ("myfid" , "str", "str2") VALUES (12, 'first string', 'second string');"""
        )
        == -1
    )


###############################################################################
# Test creating a field with the fid name (PG_USE_COPY=NO)


def test_ogr_pgdump_8():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_8.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone, options=["FID=myfid"])

    lyr.CreateField(ogr.FieldDefn("str", ogr.OFTString))
    gdal.PushErrorHandler()
    ret = lyr.CreateField(ogr.FieldDefn("myfid", ogr.OFTString))
    gdal.PopErrorHandler()
    assert ret != 0

    ret = lyr.CreateField(ogr.FieldDefn("myfid", ogr.OFTInteger))
    assert ret == 0
    lyr.CreateField(ogr.FieldDefn("str2", ogr.OFTString))

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "first string")
    feat.SetField("myfid", 10)
    feat.SetField("str2", "second string")
    gdal.SetConfigOption("PG_USE_COPY", "YES")
    ret = lyr.CreateFeature(feat)
    gdal.SetConfigOption("PG_USE_COPY", None)
    assert ret == 0
    assert feat.GetFID() == 10

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str2", "second string")
    gdal.SetConfigOption("PG_USE_COPY", "YES")
    ret = lyr.CreateFeature(feat)
    gdal.SetConfigOption("PG_USE_COPY", None)
    assert ret == 0
    if feat.GetFID() < 0:
        feat.DumpReadable()
        pytest.fail()
    if feat.GetField("myfid") != feat.GetFID():
        feat.DumpReadable()
        pytest.fail()

    # feat.SetField('str', 'foo')
    # ret = lyr.SetFeature(feat)
    # if ret != 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetFID(1)
    feat.SetField("myfid", 10)
    gdal.PushErrorHandler()
    gdal.SetConfigOption("PG_USE_COPY", "YES")
    ret = lyr.CreateFeature(feat)
    gdal.SetConfigOption("PG_USE_COPY", None)
    gdal.PopErrorHandler()
    assert ret != 0

    # gdal.PushErrorHandler()
    # ret = lyr.SetFeature(feat)
    # gdal.PopErrorHandler()
    # if ret == 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    # feat.UnsetField('myfid')
    # gdal.PushErrorHandler()
    # ret = lyr.SetFeature(feat)
    # gdal.PopErrorHandler()
    # if ret == 0:
    #    gdaltest.post_reason('fail')
    #    return 'fail'

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "first string")
    feat.SetField("myfid", 12)
    feat.SetField("str2", "second string")
    gdal.SetConfigOption("PG_USE_COPY", "YES")
    ret = lyr.CreateFeature(feat)
    gdal.SetConfigOption("PG_USE_COPY", None)
    assert ret == 0
    assert feat.GetFID() == 12

    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_8.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("ascii")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_8.sql")

    assert not (
        """CREATE TABLE "public"."test" (    "myfid" SERIAL,    CONSTRAINT "test_pk" PRIMARY KEY ("myfid") )"""
        not in sql
        or """ALTER TABLE "public"."test" ADD COLUMN "myfid" """ in sql
        or sql.find("""10\tfirst string\tsecond string""") == -1
        or sql.find(
            """INSERT INTO "public"."test" ("str2") VALUES ('second string');"""
        )
        == -1
        or sql.find("""12\tfirst string\tsecond string""") == -1
    )


###############################################################################
# Test creating a field with the fid name (PG_USE_COPY=NO)


def test_ogr_pgdump_9(pg_use_copy="YES"):

    gdal.SetConfigOption("PG_USE_COPY", pg_use_copy)

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_9.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone)

    fld = ogr.FieldDefn("str", ogr.OFTString)
    fld.SetWidth(5)
    lyr.CreateField(fld)
    fld = ogr.FieldDefn("str2", ogr.OFTString)
    lyr.CreateField(fld)

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "01234")
    lyr.CreateFeature(feat)

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "ABCDEF")
    lyr.CreateFeature(feat)

    val4 = "\u00e9\u00e9\u00e9\u00e9"
    val5 = val4 + "\u00e9"
    val6 = val5 + "\u00e9"

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", val6)
    lyr.CreateFeature(feat)

    feat = ogr.Feature(lyr.GetLayerDefn())
    feat.SetField("str", "a" + val5)
    lyr.CreateFeature(feat)

    gdal.SetConfigOption("PG_USE_COPY", None)

    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_9.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_9.sql")

    if pg_use_copy == "YES":
        eofield = "\t"
    else:
        eofield = "'"
    assert (
        """01234%s""" % eofield in sql
        and """ABCDE%s""" % eofield in sql
        and """%s%s""" % (val5, eofield) in sql
        and """%s%s""" % ("a" + val4, eofield) in sql
    )


def test_ogr_pgdump_10():
    return test_ogr_pgdump_9("NO")


###############################################################################
# Export POINT EMPTY for PostGIS 2.2


def test_ogr_pgdump_11():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_11.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbPoint)
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetGeometryDirectly(ogr.CreateGeometryFromWkt("POINT EMPTY"))
    lyr.CreateFeature(f)
    f = None
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_11.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_11.sql")

    # clang -m32 generates F8FF..., instead of F87F... for all other systems
    assert (
        "0101000000000000000000F87F000000000000F87F" in sql
        or "0101000000000000000000F8FF000000000000F8FF" in sql
    )


###############################################################################
# Test that GEOMETRY_NAME works even when the geometry column creation is
# done through CreateGeomField (#6366)
# This is important for the ogr2ogr use case when the source geometry column
# is not-nullable, and hence the CreateGeomField() interface is used.


def test_ogr_pgdump_12():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_12.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer(
        "test", geom_type=ogr.wkbNone, options=["GEOMETRY_NAME=another_name"]
    )
    lyr.CreateGeomField(ogr.GeomFieldDefn("my_geom", ogr.wkbPoint))
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_12.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_12.sql")

    assert "another_name" in sql


###############################################################################
# Test ZM support

tests_zm = [
    [
        ogr.wkbUnknown,
        [],
        "POINT ZM (1 2 3 4)",
        ["'GEOMETRY',2)", "0101000000000000000000F03F0000000000000040"],
    ],
    [
        ogr.wkbUnknown,
        ["GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        ["geography(GEOMETRY)", "0101000000000000000000F03F0000000000000040"],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYZ"],
        "POINT ZM (1 2 3 4)",
        ["'GEOMETRY',3)", "0101000080000000000000F03F00000000000000400000000000000840"],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYZ", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(GEOMETRYZ)",
            "0101000080000000000000F03F00000000000000400000000000000840",
        ],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYZ"],
        "POINT ZM (1 2 3 4)",
        ["'POINT',3)", "0101000080000000000000F03F00000000000000400000000000000840"],
    ],
    [
        ogr.wkbPoint25D,
        [],
        "POINT ZM (1 2 3 4)",
        ["'POINT',3)", "0101000080000000000000F03F00000000000000400000000000000840"],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYZ", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(POINTZ)",
            "0101000080000000000000F03F00000000000000400000000000000840",
        ],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYM"],
        "POINT ZM (1 2 3 4)",
        ["'GEOMETRY',3)", "01D1070000000000000000F03F00000000000000400000000000001040"],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYM", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(GEOMETRYM)",
            "01D1070000000000000000F03F00000000000000400000000000001040",
        ],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYM"],
        "POINT ZM (1 2 3 4)",
        ["'POINTM',3)", "01D1070000000000000000F03F00000000000000400000000000001040"],
    ],
    [
        ogr.wkbPointM,
        [],
        "POINT ZM (1 2 3 4)",
        ["'POINTM',3)", "01D1070000000000000000F03F00000000000000400000000000001040"],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYM", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(POINTM)",
            "01D1070000000000000000F03F00000000000000400000000000001040",
        ],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYZM"],
        "POINT ZM (1 2 3 4)",
        [
            "'GEOMETRY',4)",
            "01B90B0000000000000000F03F000000000000004000000000000008400000000000001040",
        ],
    ],
    [
        ogr.wkbUnknown,
        ["DIM=XYZM", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(GEOMETRYZM)",
            "01B90B0000000000000000F03F000000000000004000000000000008400000000000001040",
        ],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYZM"],
        "POINT ZM (1 2 3 4)",
        [
            "'POINT',4)",
            "01B90B0000000000000000F03F000000000000004000000000000008400000000000001040",
        ],
    ],
    [
        ogr.wkbPointZM,
        [],
        "POINT ZM (1 2 3 4)",
        [
            "'POINT',4)",
            "01B90B0000000000000000F03F000000000000004000000000000008400000000000001040",
        ],
    ],
    [
        ogr.wkbPoint,
        ["DIM=XYZM", "GEOM_TYPE=geography"],
        "POINT ZM (1 2 3 4)",
        [
            "geography(POINTZM)",
            "01B90B0000000000000000F03F000000000000004000000000000008400000000000001040",
        ],
    ],
]


@pytest.mark.parametrize("geom_type,options,wkt,expected_strings", tests_zm)
def test_ogr_pgdump_zm(geom_type, options, wkt, expected_strings):

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_13.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=geom_type, options=options)
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    lyr.CreateFeature(f)
    f = None
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_13.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_13.sql")

    for expected_string in expected_strings:
        assert expected_string in sql, (geom_type, options, wkt, expected_string)


@pytest.mark.parametrize("geom_type,options,wkt,expected_strings", tests_zm)
def test_ogr_pgdump_zm_creategeomfield(geom_type, options, wkt, expected_strings):
    if "GEOM_TYPE=geography" in options:
        return

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_13.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone, options=options)
    lyr.CreateGeomField(ogr.GeomFieldDefn("my_geom", geom_type))
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    lyr.CreateFeature(f)
    f = None
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_13.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_13.sql")

    for expected_string in expected_strings:
        assert expected_string in sql, (geom_type, options, wkt, expected_string)


###############################################################################
# Test description


def test_ogr_pgdump_14():

    # Set with DESCRIPTION layer creation option
    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_14.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer(
        "ogr_pgdump_14", geom_type=ogr.wkbPoint, options=["DESCRIPTION=foo"]
    )
    # Test that SetMetadata() and SetMetadataItem() are without effect
    lyr.SetMetadata({"DESCRIPTION": "bar"})
    lyr.SetMetadataItem("DESCRIPTION", "baz")
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_14.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_14.sql")

    assert (
        """COMMENT ON TABLE "public"."ogr_pgdump_14" IS 'foo';""" in sql
        and "bar" not in sql
        and "baz" not in sql
    )

    # Set with SetMetadataItem()
    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_14.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("ogr_pgdump_14", geom_type=ogr.wkbPoint)
    lyr.SetMetadataItem("DESCRIPTION", "bar")
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_14.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_14.sql")
    assert """COMMENT ON TABLE "public"."ogr_pgdump_14" IS 'bar';""" in sql

    # Set with SetMetadata()
    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_14.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("ogr_pgdump_14", geom_type=ogr.wkbPoint)
    lyr.SetMetadata({"DESCRIPTION": "baz"})
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_14.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_14.sql")
    assert """COMMENT ON TABLE "public"."ogr_pgdump_14" IS 'baz';""" in sql


###############################################################################
# NULL vs unset


def test_ogr_pgdump_15():

    ds = ogr.GetDriverByName("PGDump").CreateDataSource(
        "/vsimem/ogr_pgdump_15.sql", options=["LINEFORMAT=LF"]
    )
    lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone)
    lyr.CreateField(ogr.FieldDefn("str", ogr.OFTString))
    f = ogr.Feature(lyr.GetLayerDefn())
    f.SetFieldNull(0)
    lyr.CreateFeature(f)
    f = ogr.Feature(lyr.GetLayerDefn())
    lyr.CreateFeature(f)
    f = None
    ds = None

    f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_15.sql", "rb")
    sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
    gdal.VSIFCloseL(f)

    gdal.Unlink("/vsimem/ogr_pgdump_15.sql")

    assert (
        'INSERT INTO "public"."test" ("str") VALUES (NULL)' in sql
        or 'INSERT INTO "public"."test" DEFAULT VALUES' in sql
    )


###############################################################################
# Test sequence updating


def test_ogr_pgdump_16():

    for pg_use_copy in ("YES", "NO"):

        gdal.SetConfigOption("PG_USE_COPY", pg_use_copy)
        ds = ogr.GetDriverByName("PGDump").CreateDataSource(
            "/vsimem/ogr_pgdump_16.sql", options=["LINEFORMAT=LF"]
        )
        lyr = ds.CreateLayer("test", geom_type=ogr.wkbNone)
        lyr.CreateField(ogr.FieldDefn("str", ogr.OFTString))
        f = ogr.Feature(lyr.GetLayerDefn())
        f.SetFID(1)
        lyr.CreateFeature(f)
        f = None
        ds = None

        f = gdal.VSIFOpenL("/vsimem/ogr_pgdump_16.sql", "rb")
        sql = gdal.VSIFReadL(1, 10000, f).decode("utf8")
        gdal.VSIFCloseL(f)

        gdal.Unlink("/vsimem/ogr_pgdump_16.sql")

        assert (
            """SELECT setval(pg_get_serial_sequence('"public"."test"', 'ogc_fid'), MAX("ogc_fid")) FROM "public"."test";"""
            in sql
        )

    gdal.SetConfigOption("PG_USE_COPY", None)


###############################################################################
# Cleanup


def test_ogr_pgdump_cleanup():

    try:
        os.remove("tmp/tpoly.sql")
    except OSError:
        pass
    try:
        os.remove("tmp/ogr_pgdump_4.sql")
    except OSError:
        pass
