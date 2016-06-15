import unittest
import whodidwhat.path_functions


class TestFileNameFunctions(unittest.TestCase):

    def test_split_all(self):
        parts = whodidwhat.path_functions.split_all('foo/bar/daa.cpp')
        self.assertEqual(['foo', 'bar', 'daa.cpp'], parts)

    def test_get_all_folder_levels(self):
        self.assertEqual(['first'], whodidwhat.path_functions.get_all_folder_levels('first/foo.cpp'))
        self.assertEqual(['first', 'first/second'], whodidwhat.path_functions.get_all_folder_levels('first/second/foo.cpp'))

    def test_get_blame_name(self):
        self.assertEqual('https.svne.com.testsuite.test.robot',
                         whodidwhat.path_functions.get_blame_name('https://svne.com/testsuite/test.robot'))

    def test_get_blame_name_really_long_path(self):
        blame_name = whodidwhat.path_functions.get_blame_name('https://svne1.access.huawei.com/isource/svnroot/\
robotlte/trunk/testsuite/MMM/user_plane/LTE2243/LTE2243_A_j/\
LTE1234_N_j_Ab_208_53_target_pcell_and_2source_Scell_deletion_at_timing_C_when_Exchange_of_PCell_and_Scell_Intra_eNB_Inter-LSP_HO_switch_the_other_scell_to _new.robot')
        self.assertEqual(255, len(blame_name))
        self.assertEqual('s.huawei.com.isource.svnroot.\
robotlte.trunk.testsuite.MMM.user_plane.LTE2243.LTE2243_A_j.\
LTE1234_N_j_Ab_208_53_target_pcell_and_2source_Scell_deletion_at_timing_C_when_Exchange_of_PCell_and_Scell_Intra_eNB_Inter-LSP_HO_switch_the_other_scell_to _new.robot', blame_name)

if __name__ == '__main__':
    unittest.main()
