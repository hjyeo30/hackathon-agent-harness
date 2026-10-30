from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from image_analysis import read_pgm,components,write_overlay
from faults import silently_use_diagonal

class ImageTests(unittest.TestCase):
    def test_actual_bitmap_and_coordinate_oracle(self):
        pixels=read_pgm('fixtures/diagonal-edge.pgm')
        self.assertEqual((len(pixels),len(pixels[0])),(3,5))
        self.assertEqual(components(pixels),[{'area':1,'bbox':[1,0,1,0]},{'area':2,'bbox':[4,0,4,1]},{'area':1,'bbox':[0,1,0,1]}])
    def test_connectivity_fault_detected(self):
        pixels=read_pgm('fixtures/diagonal-edge.pgm')
        self.assertEqual(len(components(pixels,connectivity=8)),2)
        self.assertNotEqual(len(silently_use_diagonal(pixels)),3)
    def test_exact_threshold_and_blank(self):
        self.assertEqual(components([[127,128,129]]),[{'area':2,'bbox':[1,0,2,0]}])
        self.assertEqual(components([[0,0],[0,0]]),[])
    def test_single_pixel_and_full_image(self):
        self.assertEqual(components([[255]])[0]['area'],1)
        self.assertEqual(components([[255]*3]*2)[0]['area'],6)
    def test_bad_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.pgm'
            for raw in ['P5 1 1 255 0','P2 2 1 255 0','P2 1 1 255 999','P2 -1 1 255 0']:
                p.write_text(raw)
                with self.assertRaises(ValueError):read_pgm(p)
        with self.assertRaises(ValueError):components([[0],[0,1]])
    def test_overlay_dimensions_and_boxes(self):
        pixels=read_pgm('fixtures/diagonal-edge.pgm')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'overlay.svg';write_overlay(p,pixels,components(pixels))
            root=ET.parse(p).getroot()
            self.assertEqual(root.attrib['viewBox'],'0 0 200 120')
            boxes=[e for e in root if e.attrib.get('stroke')=='red']
            self.assertEqual(len(boxes),3)
            self.assertEqual(boxes[1].attrib['x'],'162')
