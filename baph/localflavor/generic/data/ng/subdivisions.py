# encoding: utf8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('STATES', 'AREAN_COUNCIL', 'LOCAL_GOVERMENT_AREA')

STATES = (
    ('FC', 'Abuja Federal Capital Territory'),
    ('AB', 'Abia'),
    ('AD', 'Adamawa'),
    ('AK', 'Akwa Ibom'),
    ('AN', 'Anambra'),
    ('BA', 'Bauchi'),
    ('BY', 'Bayelsa'),
    ('BE', 'Benue'),
    ('BO', 'Borno'),
    ('CR', 'Cross River'),
    ('DE', 'Delta'),
    ('EB', 'Ebonyi'),
    ('ED', 'Edo'),
    ('EK', 'Ekiti'),
    ('EN', 'Enugu'),
    ('GO', 'Gombe'),
    ('IM', 'Imo'),
    ('JI', 'Jigawa'),
    ('KD', 'Kaduna'),
    ('KN', 'Kano'),
    ('KT', 'Katsina'),
    ('KE', 'Kebbi'),
    ('KO', 'Kogi'),
    ('KW', 'Kwara'),
    ('LA', 'Lagos'),
    ('NA', 'Nasarawa'),
    ('NI', 'Niger'),
    ('OG', 'Ogun'),
    ('ON', 'Ondo'),
    ('OS', 'Osun'),
    ('OY', 'Oyo'),
    ('PL', 'Plateau'),
    ('RI', 'Rivers'),
    ('SO', 'Sokoto'),
    ('TA', 'Taraba'),
    ('YO', 'Yobe'),
    ('ZA', 'Zamfara'),
)

AREA_COUNCIL = (
    (1, 'Abaji' 'FC'),
    (2, 'Abuja' 'FC'),
    (3, 'Bwari' 'FC'),
    (4, 'Gwagwalada' 'FC'),
    (5, 'Kuje' 'FC'),
    (6, 'Kwali' 'FC'),
)

LOCAL_GOVERMENT_AREA = (
    (1, 'Aba North', 'AB'),
    (2, 'Aba South', 'AB'),
    (3, 'Arochukwu', 'AB'),
    (4, 'Bende', 'AB'),
    (5, 'Ikwuano', 'AB'),
    (6, 'Isiala Ngwa North', 'AB'),
    (7, 'Isiala Ngwa South', 'AB'),
    (8, 'Isuikwuato', 'AB'),
    (9, 'Obi Ngwa', 'AB'),
    (10, 'Ohafia', 'AB'),
    (11, 'Osisioma Ngwa', 'AB'),
    (12, 'Ugwunagbo', 'AB'),
    (13, 'Ukwa East', 'AB'),
    (14, 'Ukwa West', 'AB'),
    (15, 'Umuahia North', 'AB'),
    (16, 'Umuahia South', 'AB'),
    (17, 'Umu Nneochi', 'AB'),
    (18, 'Demsa', 'AD'),
    (19, 'Fufore', 'AD'),
    (20, 'Ganye', 'AD'),
    (21, 'Girei', 'AD'),
    (22, 'Gombi', 'AD'),
    (23, 'Guyuk', 'AD'),
    (24, 'Hong', 'AD'),
    (25, 'Jada', 'AD'),
    (26, 'Lamurde', 'AD'),
    (27, 'Madagali', 'AD'),
    (28, 'Maiha', 'AD'),
    (29, 'Mayo-Belwa', 'AD'),
    (30, 'Michika', 'AD'),
    (31, 'Mubi North', 'AD'),
    (32, 'Mubi South', 'AD'),
    (33, 'Numan', 'AD'),
    (34, 'Shelleng', 'AD'),
    (35, 'Song', 'AD'),
    (36, 'Toungo', 'AD'),
    (37, 'Yola North', 'AD'),
    (38, 'Yola South', 'AD'),
    (39, 'Abak', 'AK'),
    (40, 'Eastern Obolo', 'AK'),
    (41, 'Eket', 'AK'),
    (42, 'Esit-Eket', 'AK'),
    (43, 'Essien Udim', 'AK'),
    (44, 'Etim-Ekpo', 'AK'),
    (45, 'Etinan', 'AK'),
    (46, 'Ibeno', 'AK'),
    (47, 'Ibesikpo-Asutan', 'AK'),
    (48, 'Ibiono-Ibom', 'AK'),
    (49, 'Ika', 'AK'),
    (50, 'Ikono', 'AK'),
    (51, 'Ikot Abasi', 'AK'),
    (52, 'Ikot Ekpene', 'AK'),
    (53, 'Ini', 'AK'),
    (54, 'Itu', 'AK'),
    (55, 'Mbo', 'AK'),
    (56, 'Mkpat-Enin', 'AK'),
    (57, 'Nsit-Atai', 'AK'),
    (58, 'Nsit-Ibom', 'AK'),
    (59, 'Nsit-Ubium', 'AK'),
    (60, 'Obot-Akara', 'AK'),
    (61, 'Okobo', 'AK'),
    (62, 'Onna', 'AK'),
    (63, 'Oron', 'AK'),
    (64, 'Oruk Anam', 'AK'),
    (65, 'Ukanafun', 'AK'),
    (66, 'Udung-Uko', 'AK'),
    (67, 'Uruan', 'AK'),
    (68, 'Urue-Offong/Oruko', 'AK'),
    (69, 'Uyo', 'AK'),
    (70, 'Aguata', 'AN'),
    (71, 'Awka North', 'AN'),
    (72, 'Awka South', 'AN'),
    (73, 'Anambra East', 'AN'),
    (74, 'Anambra West', 'AN'),
    (75, 'Anaocha', 'AN'),
    (76, 'Ayamelum', 'AN'),
    (77, 'Dunukofia', 'AN'),
    (78, 'Ekwusigo', 'AN'),
    (79, 'Idemili North', 'AN'),
    (80, 'Idemili South', 'AN'),
    (81, 'Ihiala', 'AN'),
    (82, 'Njikoka', 'AN'),
    (83, 'Nnewi North', 'AN'),
    (84, 'Nnewi South', 'AN'),
    (85, 'Ogbaru', 'AN'),
    (86, 'Onitsha North', 'AN'),
    (87, 'Onitsha South', 'AN'),
    (88, 'Orumba North', 'AN'),
    (89, 'Orumba South', 'AN'),
    (90, 'Oyi', 'AN'),
    (91, 'Alkaleri', 'BA'),
    (92, 'Bauchi', 'BA'),
    (93, 'Bogoro', 'BA'),
    (94, 'Darazo', 'BA'),
    (95, 'Dass', 'BA'),
    (96, 'Gamawa', 'BA'),
    (97, 'Damban', 'BA'),
    (98, 'Ganjuwa', 'BA'),
    (99, 'Giade', 'BA'),
    (100, 'Itas/Gadau', 'BA'),
    (101, "Jama'are", 'BA'),
    (102, 'Katagum', 'BA'),
    (103, 'Kirfi', 'BA'),
    (104, 'Misau', 'BA'),
    (105, 'Ningi', 'BA'),
    (106, 'Shira', 'BA'),
    (107, 'Tafawa Balewa', 'BA'),
    (108, 'Toro', 'BA'),
    (109, 'Warji', 'BA'),
    (110, 'Zaki', 'BA'),
    (111, 'Brass', 'BY'),
    (112, 'Ekeremor', 'BY'),
    (113, 'Kolokuma/Opokuma', 'BY'),
    (114, 'Nembe', 'BY'),
    (115, 'Ogbia', 'BY'),
    (116, 'Sagbama', 'BY'),
    (117, 'Southern Ijaw', 'BY'),
    (118, 'Yenagoa', 'BY'),
    (119, 'Ado', 'BE'),
    (120, 'Agatu', 'BE'),
    (121, 'Apa', 'BE'),
    (122, 'Buruku', 'BE'),
    (123, 'Gboko', 'BE'),
    (124, 'Guma', 'BE'),
    (125, 'Gwer East', 'BE'),
    (126, 'Gwer West', 'BE'),
    (127, 'Katsina-Ala', 'BE'),
    (128, 'Konshisha', 'BE'),
    (129, 'Kwande', 'BE'),
    (130, 'Logo', 'BE'),
    (131, 'Makurdi', 'BE'),
    (132, 'Obi', 'BE'),
    (133, 'Ogbadibo', 'BE'),
    (134, 'Ohimini', 'BE'),
    (135, 'Oju', 'BE'),
    (136, 'Okpokwu', 'BE'),
    (137, 'Otukpo', 'BE'),
    (138, 'Tarka', 'BE'),
    (139, 'Ukum', 'BE'),
    (140, 'Ushongo', 'BE'),
    (141, 'Vandeikya', 'BE'),
    (142, 'Abadam', 'BO'),
    (143, 'Askira/Uba', 'BO'),
    (144, 'Bama', 'BO'),
    (145, 'Bayo', 'BO'),
    (146, 'Biu', 'BO'),
    (147, 'Chibok', 'BO'),
    (148, 'Damboa', 'BO'),
    (149, 'Dikwa', 'BO'),
    (150, 'Gubio', 'BO'),
    (151, 'Gwoza', 'BO'),
    (152, 'Guzamala', 'BO'),
    (153, 'Hawul', 'BO'),
    (154, 'Jere', 'BO'),
    (155, 'Kaga', 'BO'),
    (156, 'Kala/Balge', 'BO'),
    (157, 'Konduga', 'BO'),
    (158, 'Kukawa', 'BO'),
    (159, 'Kwaya Kusar', 'BO'),
    (160, 'Mafa', 'BO'),
    (161, 'Magumeri', 'BO'),
    (162, 'Maiduguri', 'BO'),
    (163, 'Marte', 'BO'),
    (164, 'Mobbar', 'BO'),
    (165, 'Monguno', 'BO'),
    (166, 'Ngala', 'BO'),
    (167, 'Nganzai', 'BO'),
    (168, 'Shani', 'BO'),
    (169, 'Abi', 'CR'),
    (170, 'Akamkpa', 'CR'),
    (171, 'Akpabuyo', 'CR'),
    (172, 'Bekwarra', 'CR'),
    (173, 'Biase', 'CR'),
    (174, 'Boki', 'CR'),
    (175, 'Calabar Municipal', 'CR'),
    (176, 'Calabar South', 'CR'),
    (177, 'Etung', 'CR'),
    (178, 'Ikom', 'CR'),
    (179, 'Obanliku', 'CR'),
    (180, 'Obubra', 'CR'),
    (181, 'Obudu', 'CR'),
    (182, 'Odukpani', 'CR'),
    (183, 'Ogoja', 'CR'),
    (184, 'Yakuur', 'CR'),
    (185, 'Yala', 'CR'),
    (186, 'Aniocha North', 'DE'),
    (187, 'Aniocha South', 'DE'),
    (188, 'Bomadi', 'DE'),
    (189, 'Burutu', 'DE'),
    (190, 'Ethiope East', 'DE'),
    (191, 'Ethiope West', 'DE'),
    (192, 'Okpe', 'DE'),
    (193, 'Ika North East', 'DE'),
    (194, 'Ika South', 'DE'),
    (195, 'Isoko North', 'DE'),
    (196, 'Isoko South', 'DE'),
    (197, 'Ndokwa East', 'DE'),
    (198, 'Ndokwa West', 'DE'),
    (199, 'Oshimili North', 'DE'),
    (200, 'Oshimili South', 'DE'),
    (201, 'Patani', 'DE'),
    (202, 'Sapele', 'DE'),
    (203, 'Udu', 'DE'),
    (204, 'Ughelli North', 'DE'),
    (205, 'Ughelli South', 'DE'),
    (206, 'Ukwuani', 'DE'),
    (207, 'Uvwie', 'DE'),
    (208, 'Warri North', 'DE'),
    (209, 'Warri South', 'DE'),
    (210, 'Warri South West', 'DE'),
    (211, 'Abakaliki', 'EB'),
    (212, 'Afikpo North', 'EB'),
    (213, 'Afikpo South/Edda', 'EB'),
    (214, 'Ebonyi', 'EB'),
    (215, 'Ezza North', 'EB'),
    (216, 'Ezza South', 'EB'),
    (217, 'Ikwo', 'EB'),
    (218, 'Ishielu', 'EB'),
    (219, 'Ivo', 'EB'),
    (220, 'Izzi', 'EB'),
    (221, 'Ohaozara', 'EB'),
    (222, 'Ohaukwu', 'EB'),
    (223, 'Onicha', 'EB'),
    (224, 'Akoko-Edo', 'ED'),
    (225, 'Egor', 'ED'),
    (226, 'Esan Central', 'ED'),
    (227, 'Esan North-East', 'ED'),
    (228, 'Esan South-East', 'ED'),
    (229, 'Esan West', 'ED'),
    (230, 'Etsako Central', 'ED'),
    (231, 'Etsako East', 'ED'),
    (232, 'Etsako West', 'ED'),
    (233, 'Igueben', 'ED'),
    (234, 'Ikpoba-Okha', 'ED'),
    (235, 'Oredo', 'ED'),
    (236, 'Orhionmwon', 'ED'),
    (237, 'Ovia North-East', 'ED'),
    (238, 'Ovia South-West', 'ED'),
    (239, 'Owan East', 'ED'),
    (240, 'Owan West', 'ED'),
    (241, 'Uhunmwonde', 'ED'),
    (242, 'Ado-Ekiti', 'EK'),
    (243, 'Ikere', 'EK'),
    (244, 'Oye', 'EK'),
    (245, 'Aiyekire/Gbonyin', 'EK'),
    (246, 'Efon', 'EK'),
    (247, 'Ekiti East', 'EK'),
    (248, 'Ekiti South-West', 'EK'),
    (249, 'Ekiti West', 'EK'),
    (250, 'Emure', 'EK'),
    (251, 'Ido-Osi', 'EK'),
    (252, 'Ijero', 'EK'),
    (253, 'Ikole', 'EK'),
    (254, 'Ilejemeje', 'EK'),
    (255, 'Irepodun/Ifelodun', 'EK'),
    (256, 'Ise/Orun', 'EK'),
    (257, 'Moba', 'EK'),
    (258, 'Aninri', 'EN'),
    (259, 'Awgu', 'EN'),
    (260, 'Enugu East', 'EN'),
    (261, 'Enugu North', 'EN'),
    (262, 'Enugu South', 'EN'),
    (263, 'Ezeagu', 'EN'),
    (264, 'Igbo Etiti', 'EN'),
    (265, 'Igbo Eze North', 'EN'),
    (266, 'Igbo Eze South', 'EN'),
    (267, 'Isi Uzo', 'EN'),
    (268, 'Nkanu East', 'EN'),
    (269, 'Nkanu West', 'EN'),
    (270, 'Nsukka', 'EN'),
    (271, 'Oji River', 'EN'),
    (272, 'Udenu', 'EN'),
    (273, 'Udi', 'EN'),
    (274, 'Uzo-Uwani', 'EN'),
    (275, 'Akko', 'GO'),
    (276, 'Balanga', 'GO'),
    (277, 'Billiri', 'GO'),
    (278, 'Dukku', 'GO'),
    (279, 'Funakaye', 'GO'),
    (280, 'Gombe', 'GO'),
    (281, 'Kaltungo', 'GO'),
    (282, 'Kwami', 'GO'),
    (283, 'Nafada', 'GO'),
    (284, 'Shongom', 'GO'),
    (285, 'Yamaltu/Deba', 'GO'),
    (286, 'Aboh Mbaise', 'IM'),
    (287, 'Ahiazu Mbaise', 'IM'),
    (288, 'Ehime Mbano', 'IM'),
    (289, 'Ezinihitte Mbaise', 'IM'),
    (290, 'Ideato North', 'IM'),
    (291, 'Ideato South', 'IM'),
    (292, 'Ihitte/Uboma', 'IM'),
    (293, 'Ikeduru', 'IM'),
    (294, 'Isiala Mbano', 'IM'),
    (295, 'Isu', 'IM'),
    (296, 'Mbaitoli', 'IM'),
    (297, 'Ngor Okpala', 'IM'),
    (298, 'Njaba', 'IM'),
    (299, 'Nkwerre', 'IM'),
    (300, 'Nwangele', 'IM'),
    (301, 'Obowo', 'IM'),
    (302, 'Oguta', 'IM'),
    (303, 'Ohaji/Egbema', 'IM'),
    (304, 'Okigwe', 'IM'),
    (305, 'Onuimo', 'IM'),
    (306, 'Orlu', 'IM'),
    (307, 'Orsu', 'IM'),
    (308, 'Oru East', 'IM'),
    (309, 'Oru West', 'IM'),
    (310, 'Owerri Municipal', 'IM'),
    (311, 'Owerri North', 'IM'),
    (312, 'Owerri West', 'IM'),
    (313, 'Auyo', 'JI'),
    (314, 'Babura', 'JI'),
    (315, 'Biriniwa', 'JI'),
    (316, 'Birnin Kudu', 'JI'),
    (317, 'Buji', 'JI'),
    (318, 'Dutse', 'JI'),
    (319, 'Gagarawa', 'JI'),
    (320, 'Garki', 'JI'),
    (321, 'Gumel', 'JI'),
    (322, 'Guri', 'JI'),
    (323, 'Gwaram', 'JI'),
    (324, 'Gwiwa', 'JI'),
    (325, 'Hadejia', 'JI'),
    (326, 'Jahun', 'JI'),
    (327, 'Kafin Hausa', 'JI'),
    (328, 'Kaugama', 'JI'),
    (329, 'Kazaure', 'JI'),
    (330, 'Kiri Kasama', 'JI'),
    (331, 'Kiyawa', 'JI'),
    (332, 'Maigatari', 'JI'),
    (333, 'Malam Madori', 'JI'),
    (334, 'Miga', 'JI'),
    (335, 'Ringim', 'JI'),
    (336, 'Roni', 'JI'),
    (337, 'Sule Tankarkar', 'JI'),
    (338, 'Taura', 'JI'),
    (339, 'Yankwashi', 'JI'),
    (340, 'Birnin Gwari', 'KD'),
    (341, 'Chikun', 'KD'),
    (342, 'Giwa', 'KD'),
    (343, 'Igabi', 'KD'),
    (344, 'Ikara', 'KD'),
    (345, 'Jaba', 'KD'),
    (346, "Jema'a", 'KD'),
    (347, 'Kachia', 'KD'),
    (348, 'Kaduna North', 'KD'),
    (349, 'Kaduna South', 'KD'),
    (350, 'Kagarko', 'KD'),
    (351, 'Kajuru', 'KD'),
    (352, 'Kaura', 'KD'),
    (353, 'Kauru', 'KD'),
    (354, 'Kubau', 'KD'),
    (355, 'Kudan', 'KD'),
    (356, 'Lere', 'KD'),
    (357, 'Makarfi', 'KD'),
    (358, 'Sabon Gari', 'KD'),
    (359, 'Sanga', 'KD'),
    (360, 'Soba', 'KD'),
    (361, 'Zangon Kataf', 'KD'),
    (362, 'Zaria', 'KD'),
    (363, 'Ajingi', 'KN'),
    (364, 'Albasu', 'KN'),
    (365, 'Bagwai', 'KN'),
    (366, 'Bebeji', 'KN'),
    (367, 'Bichi', 'KN'),
    (368, 'Bunkure', 'KN'),
    (369, 'Dala  ', 'KN'),
    (370, 'Dambatta ', 'KN'),
    (371, 'Dawakin Kudu', 'KN'),
    (372, 'Dawakin Tofa  ', 'KN'),
    (373, 'Doguwa  ', 'KN'),
    (374, 'Fagge', 'KN'),
    (375, 'Gabasawa ', 'KN'),
    (376, 'Garko', 'KN'),
    (377, 'Garun Mallam ', 'KN'),
    (378, 'Gaya', 'KN'),
    (379, 'Gezawa', 'KN'),
    (380, 'Gwale', 'KN'),
    (381, 'Gwarzo', 'KN'),
    (382, 'Kabo ', 'KN'),
    (383, 'Kano Municipal', 'KN'),
    (384, 'Karaye', 'KN'),
    (385, 'Kibiya', 'KN'),
    (386, 'Kiru', 'KN'),
    (387, 'Kumbotso', 'KN'),
    (388, 'Kunchi', 'KN'),
    (389, 'Kura', 'KN'),
    (390, 'Madobi', 'KN'),
    (391, 'Makoda', 'KN'),
    (392, 'Minjibir', 'KN'),
    (393, 'Nassarawa', 'KN'),
    (394, 'Rano', 'KN'),
    (395, 'Rimin Gado', 'KN'),
    (396, 'Rogo', 'KN'),
    (397, 'Shanono ', 'KN'),
    (398, 'Sumaila  ', 'KN'),
    (399, 'Takai', 'KN'),
    (400, 'Tarauni', 'KN'),
    (401, 'Tofa', 'KN'),
    (402, 'Tsanyawa', 'KN'),
    (403, 'Tudun Wada', 'KN'),
    (404, 'Ungogo', 'KN'),
    (405, 'Warawa', 'KN'),
    (406, 'Wudil', 'KN'),
    (407, 'Bakori', 'KT'),
    (408, 'Batagarawa', 'KT'),
    (409, 'Batsari', 'KT'),
    (410, 'Baure', 'KT'),
    (411, 'Bindawa', 'KT'),
    (412, 'Charanchi', 'KT'),
    (413, 'Dan Musa', 'KT'),
    (414, 'Dandume', 'KT'),
    (415, 'Danja', 'KT'),
    (416, 'Daura', 'KT'),
    (417, 'Dutsi', 'KT'),
    (418, 'Dutsin-Ma', 'KT'),
    (419, 'Faskari', 'KT'),
    (420, 'Funtua', 'KT'),
    (421, 'Ingawa', 'KT'),
    (422, 'Jibia', 'KT'),
    (423, 'Kafur', 'KT'),
    (424, 'Kaita', 'KT'),
    (425, 'Kankara', 'KT'),
    (426, 'Kankia', 'KT'),
    (427, 'Katsina', 'KT'),
    (428, 'Kurfi', 'KT'),
    (429, 'Kusada', 'KT'),
    (430, "Mai'Adua", 'KT'),
    (431, 'Malumfashi', 'KT'),
    (432, 'Mani', 'KT'),
    (433, 'Mashi', 'KT'),
    (434, 'Matazu', 'KT'),
    (435, 'Musawa', 'KT'),
    (436, 'Rimi', 'KT'),
    (437, 'Sabuwa', 'KT'),
    (438, 'Safana', 'KT'),
    (439, 'Sandamu', 'KT'),
    (440, 'Zango', 'KT'),
    (441, 'Aleiro', 'KE'),
    (442, 'Arewa Dandi', 'KE'),
    (443, 'Argungu', 'KE'),
    (444, 'Augie', 'KE'),
    (445, 'Bagudo', 'KE'),
    (446, 'Birnin Kebbi', 'KE'),
    (447, 'Bunza', 'KE'),
    (448, 'Dandi', 'KE'),
    (449, 'Fakai', 'KE'),
    (450, 'Gwandu', 'KE'),
    (451, 'Jega', 'KE'),
    (452, 'Kalgo', 'KE'),
    (453, 'Koko/Besse', 'KE'),
    (454, 'Maiyama', 'KE'),
    (455, 'Ngaski', 'KE'),
    (456, 'Sakaba', 'KE'),
    (457, 'Shanga', 'KE'),
    (458, 'Suru', 'KE'),
    (459, 'Danko/Wasagu', 'KE'),
    (460, 'Yauri', 'KE'),
    (461, 'Zuru', 'KE'),
    (462, 'Adavi', 'KO'),
    (463, 'Ajaokuta', 'KO'),
    (464, 'Ankpa', 'KO'),
    (465, 'Bassa', 'KO'),
    (466, 'Dekina', 'KO'),
    (467, 'Ibaji', 'KO'),
    (468, 'Idah', 'KO'),
    (469, 'Igalamela-Odolu', 'KO'),
    (470, 'Ijumu', 'KO'),
    (471, 'Kabba/Bunu', 'KO'),
    (472, 'Koton Karfe', 'KO'),
    (473, 'Lokoja', 'KO'),
    (474, 'Mopa-Muro', 'KO'),
    (475, 'Ofu', 'KO'),
    (476, 'Ogori/Magongo', 'KO'),
    (477, 'Okehi', 'KO'),
    (478, 'Okene', 'KO'),
    (479, 'Olamaboro', 'KO'),
    (480, 'Omala', 'KO'),
    (481, 'Yagba East', 'KO'),
    (482, 'Yagba West', 'KO'),
    (483, 'Asa', 'KW'),
    (484, 'Baruten', 'KW'),
    (485, 'Edu', 'KW'),
    (486, 'Ekiti', 'KW'),
    (487, 'Ifelodun', 'KW'),
    (488, 'Ilorin East', 'KW'),
    (489, 'Ilorin South', 'KW'),
    (490, 'Ilorin West', 'KW'),
    (491, 'Irepodun', 'KW'),
    (492, 'Isin', 'KW'),
    (493, 'Kaiama', 'KW'),
    (494, 'Moro', 'KW'),
    (495, 'Offa', 'KW'),
    (496, 'Oke Ero', 'KW'),
    (497, 'Oyun', 'KW'),
    (498, 'Pategi', 'KW'),
    (499, 'Agege', 'LA'),
    (500, 'Ajeromi-Ifelodun', 'LA'),
    (501, 'Alimosho', 'LA'),
    (502, 'Amuwo-Odofin', 'LA'),
    (503, 'Apapa', 'LA'),
    (504, 'Badagry', 'LA'),
    (505, 'Epe', 'LA'),
    (506, 'Eti-Osa', 'LA'),
    (507, 'Ibeju-Lekki', 'LA'),
    (508, 'Ifako-Ijaye', 'LA'),
    (509, 'Ikeja', 'LA'),
    (510, 'Ikorodu', 'LA'),
    (511, 'Kosofe', 'LA'),
    (512, 'Lagos Island', 'LA'),
    (513, 'Lagos Mainland', 'LA'),
    (514, 'Mushin', 'LA'),
    (515, 'Ojo', 'LA'),
    (516, 'Oshodi-Isolo', 'LA'),
    (517, 'Shomolu', 'LA'),
    (518, 'Surulere', 'LA'),
    (519, 'Akwanga', 'NA'),
    (520, 'Awe', 'NA'),
    (521, 'Doma', 'NA'),
    (522, 'Karu', 'NA'),
    (523, 'Keana', 'NA'),
    (524, 'Keffi', 'NA'),
    (525, 'Kokona', 'NA'),
    (526, 'Lafia', 'NA'),
    (527, 'Nasarawa', 'NA'),
    (528, 'Nasarawa Egon', 'NA'),
    (529, 'Obi', 'NA'),
    (530, 'Toto', 'NA'),
    (531, 'Wamba', 'NA'),
    (532, 'Agaie', 'NI'),
    (533, 'Agwara', 'NI'),
    (534, 'Bida', 'NI'),
    (535, 'Borgu', 'NI'),
    (536, 'Bosso', 'NI'),
    (537, 'Chanchaga', 'NI'),
    (538, 'Edati', 'NI'),
    (539, 'Gbako', 'NI'),
    (540, 'Gurara', 'NI'),
    (541, 'Katcha', 'NI'),
    (542, 'Kontagora', 'NI'),
    (543, 'Lapai', 'NI'),
    (544, 'Lavun', 'NI'),
    (545, 'Magama', 'NI'),
    (546, 'Mariga', 'NI'),
    (547, 'Mashegu', 'NI'),
    (548, 'Mokwa', 'NI'),
    (549, 'Munya', 'NI'),
    (550, 'Paikoro', 'NI'),
    (551, 'Rafi', 'NI'),
    (552, 'Rijau', 'NI'),
    (553, 'Shiroro', 'NI'),
    (554, 'Suleja', 'NI'),
    (555, 'Tafa', 'NI'),
    (556, 'Wushishi', 'NI'),
    (557, 'Abeokuta North', 'OG'),
    (558, 'Abeokuta South', 'OG'),
    (559, 'Ado-Odo/Ota', 'OG'),
    (560, 'Ewekoro', 'OG'),
    (561, 'Ifo', 'OG'),
    (562, 'Lisa', 'OG'),
    (563, 'Ijebu East', 'OG'),
    (564, 'Ijebu North', 'OG'),
    (565, 'Ijebu North East', 'OG'),
    (566, 'Ijebu Ode', 'OG'),
    (567, 'Ikenne', 'OG'),
    (568, 'Imeko Afon', 'OG'),
    (569, 'Ipokia', 'OG'),
    (570, 'Obafemi Owode', 'OG'),
    (571, 'Odogbolu', 'OG'),
    (572, 'Odeda', 'OG'),
    (573, 'Ogun Waterside', 'OG'),
    (574, 'Remo North', 'OG'),
    (575, 'Sagamu', 'OG'),
    (576, 'Yewa North', 'OG'),
    (577, 'Yewa South', 'OG'),
    (578, 'Akoko North-East', 'ON'),
    (579, 'Akoko North-West', 'ON'),
    (580, 'Akoko South-East', 'ON'),
    (581, 'Akoko South-West', 'ON'),
    (582, 'Akure North', 'ON'),
    (583, 'Akure South', 'ON'),
    (584, 'Ese Odo', 'ON'),
    (585, 'Idanre', 'ON'),
    (586, 'Ifedore', 'ON'),
    (587, 'Ilaje', 'ON'),
    (588, 'Ile Oluji/Okeigbo', 'ON'),
    (589, 'Irele', 'ON'),
    (590, 'Odigbo', 'ON'),
    (591, 'Okitipupa', 'ON'),
    (592, 'Ondo East', 'ON'),
    (593, 'Ondo West', 'ON'),
    (594, 'Ose', 'ON'),
    (595, 'Owo', 'ON'),
    (596, 'Aiyedaade', 'OS'),
    (597, 'Aiyedire', 'OS'),
    (598, 'Atakunmosa East', 'OS'),
    (599, 'Atakunmosa West', 'OS'),
    (600, 'Boluwaduro', 'OS'),
    (601, 'Boripe', 'OS'),
    (602, 'Ede North', 'OS'),
    (603, 'Ede South', 'OS'),
    (604, 'Egbedore', 'OS'),
    (605, 'Ejigbo', 'OS'),
    (606, 'Ife Central', 'OS'),
    (607, 'Ife East', 'OS'),
    (608, 'Ife North', 'OS'),
    (609, 'Ife South', 'OS'),
    (610, 'Ifedayo', 'OS'),
    (611, 'Ifelodun', 'OS'),
    (612, 'Ila', 'OS'),
    (613, 'Ilesa East', 'OS'),
    (614, 'Ilesa West', 'OS'),
    (615, 'Irepodun', 'OS'),
    (616, 'Irewole', 'OS'),
    (617, 'Isokan', 'OS'),
    (618, 'Iwo', 'OS'),
    (619, 'Obokun', 'OS'),
    (620, 'Odo Otin', 'OS'),
    (621, 'Ola Oluwa', 'OS'),
    (622, 'Olorunda', 'OS'),
    (623, 'Oriade', 'OS'),
    (624, 'Orolu', 'OS'),
    (625, 'Osogbo', 'OS'),
    (626, 'Afijio', 'OY'),
    (627, 'Akinyele', 'OY'),
    (628, 'Egbeda', 'OY'),
    (629, 'Ibadan North', 'OY'),
    (630, 'Ibadan North-East', 'OY'),
    (631, 'Ibadan North-West', 'OY'),
    (632, 'Ibadan South-West', 'OY'),
    (633, 'Ibadan South-East', 'OY'),
    (634, 'Ibarapa Central', 'OY'),
    (635, 'Ibarapa East Eruwa', 'OY'),
    (636, 'Ido', 'OY'),
    (637, 'Irepo', 'OY'),
    (638, 'Iseyin', 'OY'),
    (639, 'Kajola', 'OY'),
    (640, 'Lagelu', 'OY'),
    (641, 'Ogbomosho North', 'OY'),
    (642, 'Ogbomosho South', 'OY'),
    (643, 'Oyo West', 'OY'),
    (644, 'Atiba', 'OY'),
    (645, 'Atisbo', 'OY'),
    (646, 'Saki West', 'OY'),
    (647, 'Saki East', 'OY'),
    (648, 'Itesiwaju', 'OY'),
    (649, 'Iwajowa', 'OY'),
    (650, 'Ibarapa North', 'OY'),
    (651, 'Olorunsogo', 'OY'),
    (652, 'Oluyole', 'OY'),
    (653, 'Ogo Oluwa', 'OY'),
    (654, 'Surulere', 'OY'),
    (655, 'Orelope', 'OY'),
    (656, 'Ori Ire', 'OY'),
    (657, 'Oyo East', 'OY'),
    (658, 'Ona Ara', 'OY'),
    (659, 'Barkin Ladi', 'PL'),
    (660, 'Bassa', 'PL'),
    (661, 'Bokkos', 'PL'),
    (662, 'Jos East', 'PL'),
    (663, 'Jos North', 'PL'),
    (664, 'Jos South', 'PL'),
    (665, 'Kanam', 'PL'),
    (666, 'Kanke', 'PL'),
    (667, 'Langtang North', 'PL'),
    (668, 'Langtang South', 'PL'),
    (669, 'Mangu', 'PL'),
    (670, 'Mikang', 'PL'),
    (671, 'Pankshin', 'PL'),
    (672, "Qua'an Pan", 'PL'),
    (673, 'Riyom', 'PL'),
    (674, 'Shendam', 'PL'),
    (675, 'Wase', 'PL'),
    (676, 'Abua–Odual', 'RI'),
    (677, 'Ahoada West', 'RI'),
    (678, 'Ahoada East', 'RI'),
    (679, 'Akuku-Toru', 'RI'),
    (680, 'Andoni', 'RI'),
    (681, 'Asari-Toru', 'RI'),
    (682, 'Bonny', 'RI'),
    (683, 'Degema', 'RI'),
    (684, 'Eleme', 'RI'),
    (685, 'Etche', 'RI'),
    (686, 'Emohua', 'RI'),
    (687, 'Gokana', 'RI'),
    (688, 'Ikwerre', 'RI'),
    (689, 'Khana', 'RI'),
    (690, 'Obio-Akpor', 'RI'),
    (691, 'Ogba–Egbema–Ndoni', 'RI'),
    (692, 'Ogu–Bolo', 'RI'),
    (693, 'Okrika', 'RI'),
    (694, 'Omuma', 'RI'),
    (695, 'Opobo–Nkoro', 'RI'),
    (696, 'Oyigbo', 'RI'),
    (697, 'Port Harcourt', 'RI'),
    (698, 'Tai', 'RI'),
    (699, 'Binji', 'SO'),
    (700, 'Bodinga', 'SO'),
    (701, 'Dange Shuni', 'SO'),
    (702, 'Gada', 'SO'),
    (703, 'Goronyo', 'SO'),
    (704, 'Gudu', 'SO'),
    (705, 'Gwadabawa', 'SO'),
    (706, 'Illela', 'SO'),
    (707, 'Isa', 'SO'),
    (708, 'Kebbe', 'SO'),
    (709, 'Kware', 'SO'),
    (710, 'Rabah', 'SO'),
    (711, 'Sabon Birni', 'SO'),
    (712, 'Shagari', 'SO'),
    (713, 'Silame', 'SO'),
    (714, 'Sokoto North', 'SO'),
    (715, 'Sokoto South', 'SO'),
    (716, 'Tambuwal', 'SO'),
    (717, 'Tangaza', 'SO'),
    (718, 'Tureta', 'SO'),
    (719, 'Wamako', 'SO'),
    (720, 'Wurno', 'SO'),
    (721, 'Yabo', 'SO'),
    (722, 'Ardo Kola', 'TA'),
    (723, 'Bali', 'TA'),
    (724, 'Donga', 'TA'),
    (725, 'Gashaka', 'TA'),
    (726, 'Gassol', 'TA'),
    (727, 'Ibi', 'TA'),
    (728, 'Jalingo', 'TA'),
    (729, 'Karim Lamido', 'TA'),
    (730, 'Kurmi', 'TA'),
    (731, 'Lau', 'TA'),
    (732, 'Sardauna', 'TA'),
    (733, 'Takum', 'TA'),
    (734, 'Ussa', 'TA'),
    (735, 'Wukari', 'TA'),
    (736, 'Yorro', 'TA'),
    (737, 'Zing', 'TA'),
    (738, 'Bade', 'YO'),
    (739, 'Bursari', 'YO'),
    (740, 'Damaturu', 'YO'),
    (741, 'Geidam', 'YO'),
    (742, 'Gujba', 'YO'),
    (743, 'Gulani', 'YO'),
    (744, 'Fika', 'YO'),
    (745, 'Fune', 'YO'),
    (746, 'Jakusko', 'YO'),
    (747, 'Karasuwa', 'YO'),
    (748, 'Machina', 'YO'),
    (749, 'Nangere', 'YO'),
    (750, 'Nguru', 'YO'),
    (751, 'Potiskum', 'YO'),
    (752, 'Tarmuwa', 'YO'),
    (753, 'Yunusari', 'YO'),
    (754, 'Yusufari', 'YO'),
    (755, 'Anka', 'ZA'),
    (756, 'Bakura', 'ZA'),
    (757, 'Birnin Magaji/Kiyaw', 'ZA'),
    (758, 'Bukkuyum', 'ZA'),
    (759, 'Bungudu', 'ZA'),
    (760, 'Tsafe', 'ZA'),
    (761, 'Gummi', 'ZA'),
    (762, 'Gusau', 'ZA'),
    (763, 'Kaura Namoda', 'ZA'),
    (764, 'Maradun', 'ZA'),
    (765, 'Maru', 'ZA'),
    (766, 'Shinkafi', 'ZA'),
    (767, 'Talata Mafara', 'ZA'),
    (768, 'Zurmi', 'ZA'),
)
