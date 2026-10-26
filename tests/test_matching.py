import unittest

from mosaic.fields import for_to_scimago
from mosaic.matching import match_conferences, normalize_issn, trailing_acronym


def core(id_, title, acronym):
    return {"id": id_, "title": title, "acronym": acronym}


class ConferenceMatching(unittest.TestCase):
    SCIMAGO = [
        {"id": "1", "title": "Proceedings of the IEEE Computer Society Conference on Computer Vision and Pattern Recognition"},
        {"id": "2", "title": "Proceedings - Symposium on Logic in Computer Science"},
        {"id": "3", "title": "IEEE International Symposium on Information Theory - Proceedings"},
        {"id": "4", "title": "Proceedings of the Annual International Symposium on Microarchitecture, MICRO"},
        {"id": "5", "title": "Proceedings of the ACM SIGMOD International Conference on Management of Data"},
        {"id": "6", "title": "Proceedings of the Design Society"},
    ]

    def match(self, *entries):
        return match_conferences(list(entries), self.SCIMAGO)

    def test_same_event_with_proceedings_prefix(self):
        self.assertEqual(self.match(core("a", "IEEE Conference on Computer Vision and Pattern Recognition", "CVPR")), {"a": "1"})

    def test_trailing_acronym(self):
        self.assertEqual(self.match(core("a", "International Symposium on Microarchitecture", "MICRO")), {"a": "4"})

    def test_reordered_words_are_different_events(self):
        # CSL is not LICS
        self.assertEqual(self.match(core("a", "Annual Conference on Computer Science Logic", "CSL")), {})

    def test_workshop_is_not_symposium(self):
        # ITW is not ISIT
        self.assertEqual(self.match(core("a", "Information Theory Workshop", "ITW")), {})

    def test_subset_title_is_rejected(self):
        # COMAD is not SIGMOD
        self.assertEqual(self.match(core("a", "International Conference on Management of Data", "COMAD")), {})
        # ICCD is not the Design Society
        self.assertEqual(self.match(core("b", "IEEE International Conference on Computer Design", "ICCD")), {})

    def test_one_to_one(self):
        got = self.match(
            core("a", "IEEE International Symposium on Information Theory", "ISIT"),
            core("b", "International Symposium on Information Theory", "ISIT2"),
        )
        self.assertEqual(list(got.values()), ["3"])


class Helpers(unittest.TestCase):
    def test_issn(self):
        self.assertEqual(normalize_issn("1557-735x"), "1557735X")
        self.assertIsNone(normalize_issn("n/a"))

    def test_trailing_acronym_ignores_words(self):
        self.assertIsNone(trailing_acronym("IEEE Intelligent Vehicles Symposium, Proceedings"))
        self.assertEqual(trailing_acronym("Advances in Database Technology - EDBT"), "EDBT")

    def test_for_mapping(self):
        self.assertIn(("Computer Science", "Artificial Intelligence"), for_to_scimago("4602"))
        self.assertEqual(for_to_scimago("2103"), [("Arts and Humanities", None)])
        self.assertIn(("Social Sciences", "Library and Information Sciences"), for_to_scimago("0807"))


if __name__ == "__main__":
    unittest.main()
