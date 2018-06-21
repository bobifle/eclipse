#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import json
import io
import hashlib
import zipfile
import os
import logging
import difflib
import itertools
from PIL import Image
import glob

log = logging.getLogger()

data='''
{"name" : "Bob", "attributes": {"som":5, "ref": 1}}
'''

imglibs = [ 'imglib', ]

md5Template = '''<net.rptools.maptool.model.Asset>
  <id>
    <id>{{md5}}</id>
  </id>
  <name>{{name}}</name>
  <extension>{{extension}}</extension>
  <image/>
</net.rptools.maptool.model.Asset>'''


class Campaign(object):
	props_template = '''<map>
  <entry>
    <string>campaignVersion</string>
    <string>1.4.5</string>
  </entry>
  <entry>
    <string>version</string>
    <string>1.4.5.0</string>
  </entry>
</map>'''
	content_template ='''<net.rptools.maptool.util.PersistenceUtil_-PersistedCampaign>
  <campaign>
    <id>
      <baGUID>AAAAAIFwECMLAAAAAAAAAA==</baGUID>
    </id>
    <zones>
      <entry>
        <net.rptools.maptool.model.GUID>
          <baGUID>AAAAAKNwECMMAAAAAAAAAA==</baGUID>
        </net.rptools.maptool.model.GUID>
        <net.rptools.maptool.model.Zone>
          <creationTime>1529596637347</creationTime>
          <id reference="../../net.rptools.maptool.model.GUID"/>
          <grid class="net.rptools.maptool.model.SquareGrid">
            <offsetX>0</offsetX>
            <offsetY>0</offsetY>
            <size>50</size>
            <zone reference="../.."/>
            <cellShape>
              <curves>
                <sun.awt.geom.Order0>
                  <direction>1</direction>
                  <x>0.0</x>
                  <y>0.0</y>
                </sun.awt.geom.Order0>
                <sun.awt.geom.Order1>
                  <direction>1</direction>
                  <x0>0.0</x0>
                  <y0>0.0</y0>
                  <x1>0.0</x1>
                  <y1>50.0</y1>
                  <xmin>0.0</xmin>
                  <xmax>0.0</xmax>
                </sun.awt.geom.Order1>
                <sun.awt.geom.Order1>
                  <direction>-1</direction>
                  <x0>50.0</x0>
                  <y0>0.0</y0>
                  <x1>50.0</x1>
                  <y1>50.0</y1>
                  <xmin>50.0</xmin>
                  <xmax>50.0</xmax>
                </sun.awt.geom.Order1>
              </curves>
            </cellShape>
          </grid>
          <gridColor>-16777216</gridColor>
          <imageScaleX>1.0</imageScaleX>
          <imageScaleY>1.0</imageScaleY>
          <tokenVisionDistance>1000</tokenVisionDistance>
          <unitsPerCell>5</unitsPerCell>
          <drawables class="linked-list"/>
          <gmDrawables class="linked-list"/>
          <objectDrawables class="linked-list"/>
          <backgroundDrawables class="linked-list"/>
          <labels class="linked-hash-map"/>
          <tokenMap/>
          <exposedAreaMeta/>
          <tokenOrderedList class="linked-list"/>
          <initiativeList>
            <tokens/>
            <current>-1</current>
            <round>-1</round>
            <zoneId reference="../../../net.rptools.maptool.model.GUID"/>
            <fullUpdate>false</fullUpdate>
            <hideNPC>false</hideNPC>
          </initiativeList>
          <exposedArea>
            <curves/>
          </exposedArea>
          <hasFog>false</hasFog>
          <fogPaint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
            <color>-16777216</color>
          </fogPaint>
          <topology>
            <curves reference="../../exposedArea/curves"/>
          </topology>
          <backgroundPaint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
            <color>-16777216</color>
          </backgroundPaint>
          <boardPosition>
            <x>0</x>
            <y>0</y>
          </boardPosition>
          <drawBoard>true</drawBoard>
          <boardChanged>false</boardChanged>
          <name>Grasslands</name>
          <isVisible>true</isVisible>
          <visionType>OFF</visionType>
          <tokenSelection>ALL</tokenSelection>
          <height>0</height>
          <width>0</width>
        </net.rptools.maptool.model.Zone>
      </entry>
    </zones>
    <campaignProperties>
      <tokenTypeMap>
        <entry>
          <string>Basic</string>
          <list>
            <net.rptools.maptool.model.TokenProperty>
              <name>Strength</name>
              <shortName>Str</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Dexterity</name>
              <shortName>Dex</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Constitution</name>
              <shortName>Con</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Intelligence</name>
              <shortName>Int</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Wisdom</name>
              <shortName>Wis</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Charisma</name>
              <shortName>Char</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>HP</name>
              <highPriority>true</highPriority>
              <ownerOnly>true</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>AC</name>
              <highPriority>true</highPriority>
              <ownerOnly>true</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Defense</name>
              <shortName>Def</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Movement</name>
              <shortName>Mov</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Elevation</name>
              <shortName>Elv</shortName>
              <highPriority>true</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
            <net.rptools.maptool.model.TokenProperty>
              <name>Description</name>
              <shortName>Des</shortName>
              <highPriority>false</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
            </net.rptools.maptool.model.TokenProperty>
          </list>
        </entry>
      </tokenTypeMap>
      <remoteRepositoryList/>
      <lightSourcesMap class="tree-map">
        <entry>
          <string>D20</string>
          <linked-hash-map>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCYyXCvh0BAAAAAKgCIQ==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>5.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>10.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Candle - 5</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY3PCvh0CAAAAAKgCYw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>15.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>30.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Lamp - 15</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY3PCvh0DAAAAAKgCYw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>20.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>40.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Torch - 20</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY3PCvh0EAAAAAKgCYw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>20.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>40.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Everburning - 20</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY3PCvh0FAAAAAKgCYw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>30.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>60.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Lantern, Hooded - 30</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY3PCvh0GAAAAAKgCYw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>30.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                  <net.rptools.maptool.model.Light>
                    <paint class="net.rptools.maptool.model.drawing.DrawableColorPaint">
                      <color>1677721600</color>
                    </paint>
                    <facingOffset>0.0</facingOffset>
                    <radius>60.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>Sunrod - 30</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
          </linked-hash-map>
        </entry>
        <entry>
          <string>Generic</string>
          <linked-hash-map>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0HAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>5.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>5</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0IAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>15.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>15</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0JAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>20.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>20</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0KAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>30.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>30</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0LAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>40.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>40</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
            <entry>
              <net.rptools.maptool.model.GUID>
                <baGUID>wKgCY4PCvh0MAAAAAKgCAw==</baGUID>
              </net.rptools.maptool.model.GUID>
              <net.rptools.maptool.model.LightSource>
                <lightList class="linked-list">
                  <net.rptools.maptool.model.Light>
                    <facingOffset>0.0</facingOffset>
                    <radius>60.0</radius>
                    <arcAngle>360.0</arcAngle>
                    <isGM>false</isGM>
                    <ownerOnly>false</ownerOnly>
                  </net.rptools.maptool.model.Light>
                </lightList>
                <name>60</name>
                <id reference="../../net.rptools.maptool.model.GUID"/>
                <type>NORMAL</type>
                <lumens>0</lumens>
              </net.rptools.maptool.model.LightSource>
            </entry>
          </linked-hash-map>
        </entry>
      </lightSourcesMap>
      <lookupTableMap/>
      <sightTypeMap>
        <entry>
          <string>Lowlight</string>
          <net.rptools.maptool.model.SightType>
            <name>Lowlight</name>
            <multiplier>2.0</multiplier>
            <arc>0</arc>
            <distance>0.0</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
        <entry>
          <string>Darkvision</string>
          <net.rptools.maptool.model.SightType>
            <name>Darkvision</name>
            <multiplier>1.0</multiplier>
            <personalLightSource>
              <lightList class="linked-list">
                <net.rptools.maptool.model.Light>
                  <facingOffset>0.0</facingOffset>
                  <radius>60.0</radius>
                  <arcAngle>360.0</arcAngle>
                  <isGM>false</isGM>
                  <ownerOnly>false</ownerOnly>
                </net.rptools.maptool.model.Light>
              </lightList>
              <name>60</name>
              <id>
                <baGUID>wKgCY4PCvh0MAAAAAKgCAw==</baGUID>
              </id>
              <type>NORMAL</type>
              <lumens>0</lumens>
            </personalLightSource>
            <arc>0</arc>
            <distance>62.5</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
        <entry>
          <string>Normal Vision - Short Range</string>
          <net.rptools.maptool.model.SightType>
            <name>Normal Vision - Short Range</name>
            <multiplier>1.0</multiplier>
            <shape>CIRCLE</shape>
            <arc>0</arc>
            <distance>12.5</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
        <entry>
          <string>Normal</string>
          <net.rptools.maptool.model.SightType>
            <name>Normal</name>
            <multiplier>1.0</multiplier>
            <arc>0</arc>
            <distance>0.0</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
        <entry>
          <string>Conic Vision</string>
          <net.rptools.maptool.model.SightType>
            <name>Conic Vision</name>
            <multiplier>1.0</multiplier>
            <shape>CONE</shape>
            <arc>120</arc>
            <distance>0.0</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
        <entry>
          <string>Square Vision</string>
          <net.rptools.maptool.model.SightType>
            <name>Square Vision</name>
            <multiplier>1.0</multiplier>
            <shape>SQUARE</shape>
            <arc>0</arc>
            <distance>0.0</distance>
            <offset>0</offset>
          </net.rptools.maptool.model.SightType>
        </entry>
      </sightTypeMap>
      <defaultSightType>Normal</defaultSightType>
      <tokenStates class="linked-hash-map">
        <entry>
          <string>Dead</string>
          <net.rptools.maptool.client.ui.token.XTokenOverlay>
            <name>Dead</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>255</red>
              <green>0</green>
              <blue>0</blue>
              <alpha>255</alpha>
            </color>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.XTokenOverlay>
        </entry>
        <entry>
          <string>Disabled</string>
          <net.rptools.maptool.client.ui.token.XTokenOverlay>
            <name>Disabled</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>128</red>
              <green>128</green>
              <blue>128</blue>
              <alpha>255</alpha>
            </color>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.XTokenOverlay>
        </entry>
        <entry>
          <string>Hidden</string>
          <net.rptools.maptool.client.ui.token.ShadedTokenOverlay>
            <name>Hidden</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>25</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>0</red>
              <green>0</green>
              <blue>0</blue>
              <alpha>255</alpha>
            </color>
          </net.rptools.maptool.client.ui.token.ShadedTokenOverlay>
        </entry>
        <entry>
          <string>Prone</string>
          <net.rptools.maptool.client.ui.token.OTokenOverlay>
            <name>Prone</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>0</red>
              <green>0</green>
              <blue>255</blue>
              <alpha>255</alpha>
            </color>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.OTokenOverlay>
        </entry>
        <entry>
          <string>Incapacitated</string>
          <net.rptools.maptool.client.ui.token.OTokenOverlay>
            <name>Incapacitated</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color reference="../../../entry/net.rptools.maptool.client.ui.token.XTokenOverlay/color"/>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.OTokenOverlay>
        </entry>
        <entry>
          <string>Other</string>
          <net.rptools.maptool.client.ui.token.ColorDotTokenOverlay>
            <name>Other</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color reference="../../../entry/net.rptools.maptool.client.ui.token.XTokenOverlay/color"/>
            <stroke>
              <width>3.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
            <corner>SOUTH_EAST</corner>
          </net.rptools.maptool.client.ui.token.ColorDotTokenOverlay>
        </entry>
        <entry>
          <string>Other2</string>
          <net.rptools.maptool.client.ui.token.DiamondTokenOverlay>
            <name>Other2</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color reference="../../../entry/net.rptools.maptool.client.ui.token.XTokenOverlay/color"/>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.DiamondTokenOverlay>
        </entry>
        <entry>
          <string>Other3</string>
          <net.rptools.maptool.client.ui.token.YieldTokenOverlay>
            <name>Other3</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>255</red>
              <green>255</green>
              <blue>0</blue>
              <alpha>255</alpha>
            </color>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.YieldTokenOverlay>
        </entry>
        <entry>
          <string>Other4</string>
          <net.rptools.maptool.client.ui.token.TriangleTokenOverlay>
            <name>Other4</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <color>
              <red>255</red>
              <green>0</green>
              <blue>255</blue>
              <alpha>255</alpha>
            </color>
            <stroke>
              <width>5.0</width>
              <join>2</join>
              <cap>0</cap>
              <miterlimit>10.0</miterlimit>
              <dash__phase>0.0</dash__phase>
            </stroke>
          </net.rptools.maptool.client.ui.token.TriangleTokenOverlay>
        </entry>
      </tokenStates>
      <tokenBars class="linked-hash-map">
        <entry>
          <string>Health</string>
          <net.rptools.maptool.client.ui.token.TwoToneBarTokenOverlay>
            <name>Health</name>
            <order>0</order>
            <mouseover>false</mouseover>
            <opacity>100</opacity>
            <showGM>true</showGM>
            <showOwner>true</showOwner>
            <showOthers>true</showOthers>
            <increments>0</increments>
            <side>TOP</side>
            <barColor>
              <red>32</red>
              <green>180</green>
              <blue>32</blue>
              <alpha>255</alpha>
            </barColor>
            <thickness>6</thickness>
            <bgColor reference="../../../../tokenStates/entry[3]/net.rptools.maptool.client.ui.token.ShadedTokenOverlay/color"/>
          </net.rptools.maptool.client.ui.token.TwoToneBarTokenOverlay>
        </entry>
      </tokenBars>
      <characterSheets>
        <entry>
          <string>Basic</string>
          <string>net/rptools/maptool/client/ui/forms/basicCharacterSheet.xml</string>
        </entry>
      </characterSheets>
      <initiativeOwnerPermissions>false</initiativeOwnerPermissions>
      <initiativeMovementLock>false</initiativeMovementLock>
    </campaignProperties>
    <macroButtonProperties/>
    <macroButtonLastIndex>0</macroButtonLastIndex>
  </campaign>
  <assetMap/>
  <currentZoneId reference="../campaign/zones/entry/net.rptools.maptool.model.GUID"/>
  <currentView>
    <oneToOneScale>1.0</oneToOneScale>
    <scale>1.0</scale>
    <scaleIncrement>0.075</scaleIncrement>
    <zoomLevel>0</zoomLevel>
    <offsetX>0</offsetX>
    <offsetY>0</offsetY>
    <width>0</width>
    <height>0</height>
    <initialized>false</initialized>
  </currentView>
</net.rptools.maptool.util.PersistenceUtil_-PersistedCampaign>'''

	@property
	def name(self): return 'dft'

	@property
	def content_xml(self):
		t = jinja2.Template(self.content_template)
		content = t.render(cmpgn=self)
		return content or ''

	@property
	def properties_xml(self):
		t = jinja2.Template(self.props_template)
		content = t.render(cmpgn=self)
		return content or ''
	
	def zipme(self):
		"""Zip the token into a rptok file."""
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.cmpgn'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)


class Prop(object):
	def __init__(self, name, value):
		self.name = name
		self.value = value
	def __repr__(self): return '%s<%s,%s>' % (self.__class__.__name__, self.name, self.value)
	def render(self):
		return jinja2.Template('''      <entry>
        <string>{{prop.name.lower()}}</string>
        <net.rptools.CaseInsensitiveHashMap_-KeyValue>
          <key>{{prop.name}}</key>
          <value class="string">{{prop.value}}</value>
          <outer-class reference="../../../.."/>
        </net.rptools.CaseInsensitiveHashMap_-KeyValue>
      </entry>''').render(prop=self)

class Token(object):
	sentinel = object()

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self.name = 'defaultName'
		self.size = 'medium'

	# XXX system dependant ?
	@property
	def size_guid(self):
		# XXX may depend on the maptool version
		return {
			'tiny':       'fwABAc5lFSoDAAAAKgABAA==',
			'small':      'fwABAc5lFSoEAAAAKgABAA==',
			'medium':     'fwABAc9lFSoFAAAAKgABAQ==',
			'large':      'fwABAdBlFSoGAAAAKgABAA==',
			'huge':       'fwABAdBlFSoHAAAAKgABAA==',
			'gargantuan': 'fwABAdFlFSoIAAAAKgABAQ==',
		}[self.size.lower()]

	@property
	def macros(self): raise NotImplementedError

	@property
	def props(self): raise NotImplementedError

	@property
	def states(self): raise NotImplementedError

	@property
	def guid(self):	return ''

	@property
	def content_xml(self):
		with open(os.path.join('src','content.template')) as template:
			t = jinja2.Template(template.read())
		content = t.render(token=self)
		return content or ''

	@property
	def properties_xml(self):
		with open(os.path.join('src', 'properties.template')) as template:
			 t = jinja2.Template(template.read())
			 return t.render()

	@property
	def md5(self):
		if self._md5 is self.sentinel: # cache this expensive property
			out = io.BytesIO()
			self.img.save(out, format='png')
			self._md5 = hashlib.md5(out.getvalue()).hexdigest()
		return self._md5

	def zipme(self):
		"""Zip the token into a rptok file."""
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.rptok'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)
			log.debug('Token image md5 %s' % self.md5)
			# default image for the token, right now it's a brown bear
			# zip the xml file named with the md5 containing the asset properties
			zipme.writestr('assets/%s' % self.md5, jinja2.Template(md5Template).render(name=self.name, extension='png', md5=self.md5))
			# zip the img itself
			out = io.BytesIO() ; self.img.save(out, format='PNG')
			zipme.writestr('assets/%s.png' % self.md5, out.getvalue())
			# build thumbnails
			out = io.BytesIO()
			im = self.img.copy() ; im.thumbnail((50,50)) ; im.save(out, format='PNG')
			zipme.writestr('thumbnail', out.getvalue())
			out = io.BytesIO()
			im = self.img.copy() ; im.thumbnail((500,500)) ; im.save(out, format='PNG')
			zipme.writestr('thumbnail_large', out.getvalue())

	@property
	def img(self):
		# try to fetch an appropriate image from the imglib directory
		# using a stupid heuristic: the image / token.name match ratio
		if self._img is self.sentinel: # cache to property
			# compute the diff ratio for the given name compared to the token name
			ratio = lambda name: difflib.SequenceMatcher(None, name.lower(), self.name.lower()).ratio()
			# morph "/abc/def/anyfile.png" into "anyfile"
			short_name = lambda full_path: os.path.splitext(os.path.basename(full_path))[0]
			# list of all img files
			files = itertools.chain(*(glob.glob(os.path.join(os.path.expanduser(imglib), '*.png')) for imglib in imglibs))
			bratio=0
			if files:
				# generate the diff ratios
				ratios = ((f, ratio(short_name(f))) for f in files)
				# pickup the best match, it's a tuple (fpath, ratio)
				bfpath, bratio = max(itertools.chain(ratios, [('', 0)]), key = lambda i: i[1])
				log.debug("Best match from the img lib is %s(%s)" % (bfpath, bratio))
			if bratio > 0.8:
				self._img = Image.open(bfpath, 'r')
			else:
				self._img = Image.open(os.path.join('imglib', 'dft.png'), 'r')
		return self._img

class Character(Token):
	"Eclipse Character"

	@classmethod
	def from_json(cls, dct):
		if "name" in dct and "attributes" in dct:
			ret = cls()
			for k,v in dct.iteritems(): setattr(ret, k, v)
			return ret
		return dct

	def __repr__(self): return 'Char<%s>' % self.name

	@property
	def props(self): return [Prop('som', self.attributes['som'])]

	@property
	def states(self): return []

	@property
	def macros(self): return []

if __name__== '__main__':
	logging.basicConfig(level=logging.INFO)
	x = json.loads(data, object_hook = Character.from_json)
	x.zipme()
	Campaign().zipme()
