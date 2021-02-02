import unittest
from rfcyaml.RFC import RFC


class TestRFC(unittest.TestCase):
    def setUp(self):
        self.rfc = RFC(20)

    def test_get_text(self):
        text = self.rfc.get_text()
        self.assertEqual(
            text[:45],
            'USA Standard Code for Information Interchange'
        )
        self.assertEqual(
            len(text),
            16300
        )

    def test_get_structure(self):
        structure = self.rfc.get_structure()
        self.assertEqual(
            structure,
            [
                ['__initial_text__', []],
                ['USA Standard Code for Information Interchange', []],
                ['1. Scope', []],
                ['2. Standard Code', []],
                ['3. Character Representation and Code Identification', []],
                ['4. Legend',
                    [
                        ['4.1 Control Characters', []],
                        ['4.2 Graphic Characters', []]
                    ]
                ],
                ['5. Definitions',
                    [
                        ['5.1 General', []],
                        ['5.2 Control Characters', []],
                        ['5.3 Graphic Characters', []]
                    ]
                ],
                ['6. General Considerations', []]
            ]
        )

if __name__ == '__main__':
    unittest.main()
