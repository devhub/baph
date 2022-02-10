# encoding: utf8
from __future__ import unicode_literals

from __future__ import absolute_import
from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('PROVINCES', 'DISTRICTS', 'CORREGIMIENTOS')

PA_PROVINCES = (
  ('1', _('Bocas del Toro')),
  ('4', _('Chiriquí')),
  ('2', _('Coclé')),
  ('3', _('Colón')),
  ('5', _('Darién')),
  ('6', _('Herrera')),
  ('7', _('Los Santos')),
  ('8', _('Panamá')),
  ('9', _('Veraguas')),
)

PA_INDIGENOUS = (
  ('EM', _('Emberá')),
  ('KY', _('Kuna Yala')),
  ('NB', _('Ngäbe-Buglé')),
)

PROVINCES = tuple(sorted(PA_PROVINCES + PA_INDIGENOUS, key=lambda obj: obj[1]))

DISTRICTS = (
  ('1', _('Bocas del Toro'), '1'),
  ('2', _('Changuinola'), '1'),
  ('3', _('Chiriquí Grande'), '1'),
  ('4', _('Alanje'), '4'),
  ('5', _('Barú'), '4'),
  ('6', _('Boquerón'), '4'),
  ('7', _('Boquete'), '4'),
  ('8', _('Bugaba'), '4'),
  ('9', _('David'), '4'),
  ('10', _('Dolega'), '4'),
  ('11', _('Gualaca'), '4'),
  ('12', _('Remedios'), '4'),
  ('13', _('Renacimiento'), '4'),
  ('14', _('San Félix'), '4'),
  ('15', _('San Lorenzo'), '4'),
  ('16', _('Tolé'), '4'),
  ('17', _('Aguadulce'), '2'),
  ('18', _('Antón'), '2'),
  ('19', _('La Pintada'), '2'),
  ('20', _('Natá'), '2'),
  ('21', _('Olá'), '2'),
  ('22', _('Penonomé'), '2'),
  ('23', _('Chagres'), '3'),
  ('24', _('Ciudad de Colón'), '3'),
  ('25', _('Donoso'), '3'),
  ('26', _('Portobelo'), '3'),
  ('27', _('Resto del Distrito'), '3'),
  ('28', _('Santa Isabel'), '3'),
  ('29', _('Chepigana'), '5'),
  ('30', _('Pinogana'), '5'),
  ('31', _('Cémaco'), 'EM'),
  ('32', _('Sambú'), 'EM'),
  ('33', _('Chitré'), '6'),
  ('34', _('Las Minas'), '6'),
  ('35', _('Los Pozos'), '6'),
  ('36', _('Ocú'), '6'),
  ('37', _('Parita'), '6'),
  ('38', _('Pesé'), '6'),
  ('39', _('Santa María'), '6'),
  ('40', _('Comarca Kuna Yala'), 'KY'),
  ('41', _('Guararé'), '7'),
  ('42', _('Las Tablas'), '7'),
  ('43', _('Los Santos'), '7'),
  ('44', _('Macaracas'), '7'),
  ('45', _('Pedasí'), '7'),
  ('46', _('Pocrí'), '7'),
  ('47', _('Tonosí'), '7'),
  ('48', _('Besiko'), 'NB'),
  ('49', _('Kankintú'), 'NB'),
  ('50', _('Kusapín'), 'NB'),
  ('51', _('Mironó'), 'NB'),
  ('52', _('Müna'), 'NB'),
  ('53', _('Nole Duima'), 'NB'),
  ('54', _('Ñürüm'), 'NB'),
  ('55', _('Arraiján'), '8'),
  ('56', _('Balboa'), '8'),
  ('57', _('Capira'), '8'),
  ('58', _('Chame'), '8'),
  ('59', _('Chepo'), '8'),
  ('60', _('Chimán'), '8'),
  ('61', _('Ciudad de Panamá'), '8'),
  ('62', _('La Chorrera'), '8'),
  ('63', _('Resto del Distrito'), '8'),
  ('64', _('San Carlos'), '8'),
  ('65', _('San Miguelito'), '8'),
  ('66', _('Taboga'), '8'),
  ('67', _('Atalaya'), '9'),
  ('68', _('Calobre'), '9'),
  ('69', _('Cañazas'), '9'),
  ('70', _('La Mesa'), '9'),
  ('71', _('Las Palmas'), '9'),
  ('72', _('Mariato'), '9'),
  ('73', _('Montijo'), '9'),
  ('74', _('Río de Jesús'), '9'),
  ('75', _('San Francisco'), '9'),
  ('76', _('Santa Fé'), '9'),
  ('77', _('Santiago'), '9'),
  ('78', _('Soná'), '9'),
)

CORREGIMIENTOS = (
  ('1', _('Bastimentos'), '1', '1'),
  ('2', _('Bocas del Toro'), '1', '1'),
  ('3', _('Cauchero'), '1', '1'),
  ('4', _('Punta Laurel'), '1', '1'),
  ('5', _('Tierra Oscura'), '1', '1'),
  ('6', _('Almirante'), '1', '2'),
  ('7', _('Changuinola'), '1', '2'),
  ('8', _('Cochigró'), '1', '2'),
  ('9', _('El Empalme'), '1', '2'),
  ('10', _('Guabito'), '1', '2'),
  ('11', _('La Gloria'), '1', '2'),
  ('12', _('Las Delicias'), '1', '2'),
  ('13', _('Las Tablas'), '1', '2'),
  ('14', _('Nance del Risco'), '1', '2'),
  ('15', _('Teribe'), '1', '2'),
  ('16', _('Valle de Agua Arriba'), '1', '2'),
  ('17', _('Valle del Risco'), '1', '2'),
  ('18', _('Bajo Cedro'), '1', '3'),
  ('19', _('Chiriquí Grande'), '1', '3'),
  ('20', _('Miramar'), '1', '3'),
  ('21', _('Punta Peña'), '1', '3'),
  ('22', _('Punta Robalo'), '1', '3'),
  ('23', _('Rambala'), '1', '3'),
  ('24', _('Alanje'), '4', '4'),
  ('25', _('Canta Gallo'), '4', '4'),
  ('26', _('Divalá'), '4', '4'),
  ('27', _('El Tejar'), '4', '4'),
  ('28', _('Guarumal'), '4', '4'),
  ('29', _('Nuevo México'), '4', '4'),
  ('30', _('Palo Grande'), '4', '4'),
  ('31', _('Querévalo'), '4', '4'),
  ('32', _('Santo Tomás'), '4', '4'),
  ('33', _('Baco'), '4', '5'),
  ('34', _('Limones'), '4', '5'),
  ('35', _('Progreso'), '4', '5'),
  ('36', _('Puerto Armuelles'), '4', '5'),
  ('37', _('Rodolfo Aguilar Delgado'), '4', '5'),
  ('38', _('Boquerón'), '4', '6'),
  ('39', _('Bágala'), '4', '6'),
  ('40', _('Cordillera'), '4', '6'),
  ('41', _('Guabal'), '4', '6'),
  ('42', _('Guayabal'), '4', '6'),
  ('43', _('Paraíso'), '4', '6'),
  ('44', _('Pedregal'), '4', '6'),
  ('45', _('Tijeras'), '4', '6'),
  ('46', _('Alto Boquete'), '4', '7'),
  ('47', _('Bajo Boquete'), '4', '7'),
  ('48', _('Caldera'), '4', '7'),
  ('49', _('Jaramillo'), '4', '7'),
  ('50', _('Los Naranjos'), '4', '7'),
  ('51', _('Palmira'), '4', '7'),
  ('52', _('Aserrío de Gariché'), '4', '8'),
  ('53', _('Bugaba'), '4', '8'),
  ('54', _('Cerro Punta'), '4', '8'),
  ('55', _('El Bongo'), '4', '8'),
  ('56', _('Gómez'), '4', '8'),
  ('57', _('La Concepción'), '4', '8'),
  ('58', _('La Estrella'), '4', '8'),
  ('59', _('San Andrés'), '4', '8'),
  ('60', _('Santa Marta'), '4', '8'),
  ('61', _('Santa Rosa'), '4', '8'),
  ('62', _('Santo Domingo'), '4', '8'),
  ('63', _('Sortová'), '4', '8'),
  ('64', _('Volcán'), '4', '8'),
  ('65', _('Bijagual'), '4', '9'),
  ('66', _('Chiriquí'), '4', '9'),
  ('67', _('Cochea'), '4', '9'),
  ('68', _('David'), '4', '9'),
  ('69', _('Guacá'), '4', '9'),
  ('70', _('Las Lomas'), '4', '9'),
  ('71', _('Pedregal'), '4', '9'),
  ('72', _('San Carlos'), '4', '9'),
  ('73', _('San Pablo Nuevo'), '4', '9'),
  ('74', _('San Pablo Viejo'), '4', '9'),
  ('75', _('Dolega'), '4', '10'),
  ('76', _('Dos Ríos'), '4', '10'),
  ('77', _('Los Algarrobos'), '4', '10'),
  ('78', _('Los Anastacios'), '4', '10'),
  ('79', _('Potrerillos'), '4', '10'),
  ('80', _('Potrerillos Abajo'), '4', '10'),
  ('81', _('Rovira'), '4', '10'),
  ('82', _('Tinajas'), '4', '10'),
  ('83', _('Gualaca'), '4', '11'),
  ('84', _('Hornito'), '4', '11'),
  ('85', _('Los Angeles'), '4', '11'),
  ('86', _('Paja de Sombrero'), '4', '11'),
  ('87', _('Rincón'), '4', '11'),
  ('88', _('El Nancito'), '4', '12'),
  ('89', _('El Porvenir'), '4', '12'),
  ('90', _('El Puerto'), '4', '12'),
  ('91', _('Remedios'), '4', '12'),
  ('92', _('Santa Lucia'), '4', '12'),
  ('93', _('Breñon'), '4', '13'),
  ('94', _('Cañas Gordas'), '4', '13'),
  ('95', _('Dominical'), '4', '13'),
  ('96', _('Monte Lirio'), '4', '13'),
  ('97', _('Plaza Caisán'), '4', '13'),
  ('98', _('Río Sereno'), '4', '13'),
  ('99', _('Santa Clara'), '4', '13'),
  ('100', _('Santa Cruz'), '4', '13'),
  ('101', _('Juay'), '4', '14'),
  ('102', _('Lajas Adentro'), '4', '14'),
  ('103', _('Las Lajas'), '4', '14'),
  ('104', _('San Félix'), '4', '14'),
  ('105', _('Santa Cruz'), '4', '14'),
  ('106', _('Boca Chica'), '4', '15'),
  ('107', _('Boca del Monte'), '4', '15'),
  ('108', _('Horconcitos'), '4', '15'),
  ('109', _('San Juan'), '4', '15'),
  ('110', _('San Lorenzo'), '4', '15'),
  ('111', _('Bella Vista'), '4', '16'),
  ('112', _('Cerro Viejo'), '4', '16'),
  ('113', _('El Cristo'), '4', '16'),
  ('114', _('Justo Fidel Palacios'), '4', '16'),
  ('115', _('Lajas de Tolé'), '4', '16'),
  ('116', _('Potrero de Caña'), '4', '16'),
  ('117', _('Quebrada de Piedra'), '4', '16'),
  ('118', _('Tolé'), '4', '16'),
  ('119', _('Veladero'), '4', '16'),
  ('120', _('Aguadulce'), '2', '17'),
  ('121', _('Barrios Unidos'), '2', '17'),
  ('122', _('El Cristo'), '2', '17'),
  ('123', _('El Roble'), '2', '17'),
  ('124', _('Pocrí'), '2', '17'),
  ('125', _('Antón'), '2', '18'),
  ('126', _('Caballero'), '2', '18'),
  ('127', _('Cabuya'), '2', '18'),
  ('128', _('El Chirú'), '2', '18'),
  ('129', _('El Retiro'), '2', '18'),
  ('130', _('El Valle'), '2', '18'),
  ('131', _('Juan Díaz'), '2', '18'),
  ('132', _('Río Hato'), '2', '18'),
  ('133', _('San Juan de Dios'), '2', '18'),
  ('134', _('Santa Rita'), '2', '18'),
  ('135', _('El Harino'), '2', '19'),
  ('136', _('El Potrero'), '2', '19'),
  ('137', _('La Pintada'), '2', '19'),
  ('138', _('Las Lomas'), '2', '19'),
  ('139', _('Llano Grande'), '2', '19'),
  ('140', _('Piedras Gordas'), '2', '19'),
  ('141', _('Capellanía'), '2', '20'),
  ('142', _('El Caño'), '2', '20'),
  ('143', _('Guzmán'), '2', '20'),
  ('144', _('Las Huacas'), '2', '20'),
  ('145', _('Natá'), '2', '20'),
  ('146', _('Toza'), '2', '20'),
  ('147', _('El Copé'), '2', '21'),
  ('148', _('El Palmar'), '2', '21'),
  ('149', _('El Picacho'), '2', '21'),
  ('150', _('La Pava'), '2', '21'),
  ('151', _('Olá'), '2', '21'),
  ('152', _('Cañaveral'), '2', '22'),
  ('153', _('Chiguirí Arriba'), '2', '22'),
  ('154', _('Coclé'), '2', '22'),
  ('155', _('El Coco'), '2', '22'),
  ('156', _('Pajonal'), '2', '22'),
  ('157', _('Penonomé'), '2', '22'),
  ('158', _('Río Grande'), '2', '22'),
  ('159', _('Río Indio'), '2', '22'),
  ('160', _('Toabré'), '2', '22'),
  ('161', _('Tulú'), '2', '22'),
  ('162', _('Achiote'), '3', '23'),
  ('163', _('El Guabo'), '3', '23'),
  ('164', _('La Encantada'), '3', '23'),
  ('165', _('Nuevo Chagres'), '3', '23'),
  ('166', _('Palmas Bellas'), '3', '23'),
  ('167', _('Piña'), '3', '23'),
  ('168', _('Salud'), '3', '23'),
  ('169', _('Barrio Norte'), '3', '24'),
  ('170', _('Barrio Sur'), '3', '24'),
  ('171', _('Coclé del Norte'), '3', '25'),
  ('172', _('El Guásimo'), '3', '25'),
  ('173', _('Gobea'), '3', '25'),
  ('174', _('Miguel de la Borda'), '3', '25'),
  ('175', _('Río Indio'), '3', '25'),
  ('176', _('San José del General'), '3', '25'),
  ('177', _('Cacique'), '3', '26'),
  ('178', _('Isla Grande'), '3', '26'),
  ('179', _('María Chiquita'), '3', '26'),
  ('180', _('Portobelo'), '3', '26'),
  ('181', _('Puerto Lindo o Garrote'), '3', '26'),
  ('182', _('Buena Vista'), '3', '27'),
  ('183', _('Cativá'), '3', '27'),
  ('184', _('Ciricito'), '3', '27'),
  ('185', _('Cristóbal'), '3', '27'),
  ('186', _('Escobal'), '3', '27'),
  ('187', _('Limón'), '3', '27'),
  ('188', _('Nueva Providencia'), '3', '27'),
  ('189', _('Puerto Pilón'), '3', '27'),
  ('190', _('Sabanitas'), '3', '27'),
  ('191', _('Salamanca'), '3', '27'),
  ('192', _('San Juan'), '3', '27'),
  ('193', _('Santa Rosa'), '3', '27'),
  ('194', _('Cuango'), '3', '28'),
  ('195', _('Miramar'), '3', '28'),
  ('196', _('Nombre de Dios'), '3', '28'),
  ('197', _('Palenque'), '3', '28'),
  ('198', _('Palmira'), '3', '28'),
  ('199', _('Playa Chiquita'), '3', '28'),
  ('200', _('Santa Isabel'), '3', '28'),
  ('201', _('Viento Frío'), '3', '28'),
  ('202', _('Agua Fría'), '5', '29'),
  ('203', _('Camogantí'), '5', '29'),
  ('204', _('Chepigana'), '5', '29'),
  ('205', _('Cucunatí'), '5', '29'),
  ('206', _('Garachiné'), '5', '29'),
  ('207', _('Jaqué'), '5', '29'),
  ('208', _('La Palma'), '5', '29'),
  ('209', _('Puerto Piña'), '5', '29'),
  ('210', _('Río Congo'), '5', '29'),
  ('211', _('Río Congo Arriba'), '5', '29'),
  ('212', _('Río Iglesias'), '5', '29'),
  ('213', _('Sambú'), '5', '29'),
  ('214', _('Santa Fé'), '5', '29'),
  ('215', _('Setegantí'), '5', '29'),
  ('216', _('Taimatí'), '5', '29'),
  ('217', _('Tucutí'), '5', '29'),
  ('218', _('Boca de Cupé'), '5', '30'),
  ('219', _('Comarca Kuna de Wargandí'), '5', '30'),
  ('220', _('El Real de Santa María'), '5', '30'),
  ('221', _('Metetí'), '5', '30'),
  ('222', _('Paya'), '5', '30'),
  ('223', _('Pinogana'), '5', '30'),
  ('224', _('Púcuro'), '5', '30'),
  ('225', _('Yape'), '5', '30'),
  ('226', _('Yaviza'), '5', '30'),
  ('227', _('Cirilo Guainora'), 'EM', '31'),
  ('228', _('Lajas Blancas'), 'EM', '31'),
  ('229', _('Manuel Ortega'), 'EM', '31'),
  ('230', _('Jingurudó'), 'EM', '32'),
  ('231', _('Río Sábalo'), 'EM', '32'),
  ('232', _('Chitré'), '6', '33'),
  ('233', _('La Arena'), '6', '33'),
  ('234', _('Llano Bonito'), '6', '33'),
  ('235', _('Monagrillo'), '6', '33'),
  ('236', _('San Juan Bautista'), '6', '33'),
  ('237', _('Chepo'), '6', '34'),
  ('238', _('Chumical'), '6', '34'),
  ('239', _('El Toro'), '6', '34'),
  ('240', _('Las Minas'), '6', '34'),
  ('241', _('Leones'), '6', '34'),
  ('242', _('Quebrada El Ciprián'), '6', '34'),
  ('243', _('Quebrada del Rosario'), '6', '34'),
  ('244', _('Capurí'), '6', '35'),
  ('245', _('El Calabacito'), '6', '35'),
  ('246', _('El Cedro'), '6', '35'),
  ('247', _('La Arena'), '6', '35'),
  ('248', _('La Pitaloza'), '6', '35'),
  ('249', _('Las Llanas'), '6', '35'),
  ('250', _('Los Cerritos'), '6', '35'),
  ('251', _('Los Cerros de Paja'), '6', '35'),
  ('252', _('Los Pozos'), '6', '35'),
  ('253', _('Cerro Largo'), '6', '36'),
  ('254', _('El Tijera'), '6', '36'),
  ('255', _('Llano Grande'), '6', '36'),
  ('256', _('Los Llanos'), '6', '36'),
  ('257', _('Menchaca'), '6', '36'),
  ('258', _('Ocú'), '6', '36'),
  ('259', _('Peñas Chatas'), '6', '36'),
  ('260', _('Cabuya'), '6', '37'),
  ('261', _('Llano de la Cruz'), '6', '37'),
  ('262', _('Los Castillos'), '6', '37'),
  ('263', _('Parita'), '6', '37'),
  ('264', _('París'), '6', '37'),
  ('265', _('Portobelillo'), '6', '37'),
  ('266', _('Potuga'), '6', '37'),
  ('267', _('El Barrero'), '6', '38'),
  ('268', _('El Ciruelo'), '6', '38'),
  ('269', _('El Pedregoso'), '6', '38'),
  ('270', _('El Pájaro'), '6', '38'),
  ('271', _('Las Cabras'), '6', '38'),
  ('272', _('Pesé'), '6', '38'),
  ('273', _('Rincón Hondo'), '6', '38'),
  ('274', _('Sabanagrande'), '6', '38'),
  ('275', _('Chupampa'), '6', '39'),
  ('276', _('El Limón'), '6', '39'),
  ('277', _('El Rincón'), '6', '39'),
  ('278', _('Los Canelos'), '6', '39'),
  ('279', _('Santa María'), '6', '39'),
  ('280', _('Ailigandí'), 'KY', '40'),
  ('281', _('Narganá'), 'KY', '40'),
  ('282', _('Puerto Obaldía'), 'KY', '40'),
  ('283', _('Tubualá'), 'KY', '40'),
  ('284', _('El Espinal'), '7', '41'),
  ('285', _('El Hato'), '7', '41'),
  ('286', _('El Macano'), '7', '41'),
  ('287', _('Guararé'), '7', '41'),
  ('288', _('Guararé Arriba'), '7', '41'),
  ('289', _('La Enea'), '7', '41'),
  ('290', _('La Pasera'), '7', '41'),
  ('291', _('Las Trancas'), '7', '41'),
  ('292', _('Llano Abajo'), '7', '41'),
  ('293', _('Perales'), '7', '41'),
  ('294', _('Bajo Corral'), '7', '42'),
  ('295', _('Bayano'), '7', '42'),
  ('296', _('El Carate'), '7', '42'),
  ('297', _('El Cocal'), '7', '42'),
  ('298', _('El Manantial'), '7', '42'),
  ('299', _('El Muñoz'), '7', '42'),
  ('300', _('El Pedregoso'), '7', '42'),
  ('301', _('La Laja'), '7', '42'),
  ('302', _('La Miel'), '7', '42'),
  ('303', _('La Palma'), '7', '42'),
  ('304', _('La Tiza'), '7', '42'),
  ('305', _('Las Palmitas'), '7', '42'),
  ('306', _('Las Tablas'), '7', '42'),
  ('307', _('Las Tablas Abajo'), '7', '42'),
  ('308', _('Nuario'), '7', '42'),
  ('309', _('Palmira'), '7', '42'),
  ('310', _('Peña Blanca'), '7', '42'),
  ('311', _('Río Hondo'), '7', '42'),
  ('312', _('San José'), '7', '42'),
  ('313', _('San Miguel'), '7', '42'),
  ('314', _('Santo Domingo'), '7', '42'),
  ('315', _('Sesteadero'), '7', '42'),
  ('316', _('Valle Rico'), '7', '42'),
  ('317', _('Vallerriquito'), '7', '42'),
  ('318', _('Agua Buena'), '7', '43'),
  ('319', _('El Guásimo'), '7', '43'),
  ('320', _('La Colorada'), '7', '43'),
  ('321', _('La Espigadilla'), '7', '43'),
  ('322', _('La Villa de los Santos'), '7', '43'),
  ('323', _('Las Cruces'), '7', '43'),
  ('324', _('Las Guabas'), '7', '43'),
  ('325', _('Llano Largo'), '7', '43'),
  ('326', _('Los Angeles'), '7', '43'),
  ('327', _('Los Olivos'), '7', '43'),
  ('328', _('Sabanagrande'), '7', '43'),
  ('329', _('Santa Ana'), '7', '43'),
  ('330', _('Tres Quebradas'), '7', '43'),
  ('331', _('Villa Lourdes'), '7', '43'),
  ('332', _('Bahía Honda'), '7', '44'),
  ('333', _('Bajos de Güera'), '7', '44'),
  ('334', _('Chupá'), '7', '44'),
  ('335', _('Corozal'), '7', '44'),
  ('336', _('El Cedro'), '7', '44'),
  ('337', _('Espino Amarillo'), '7', '44'),
  ('338', _('La Mesa'), '7', '44'),
  ('339', _('Las Palmas'), '7', '44'),
  ('340', _('Llano de Piedra'), '7', '44'),
  ('341', _('Macaracas'), '7', '44'),
  ('342', _('Mogollón'), '7', '44'),
  ('343', _('Los Asientos'), '7', '45'),
  ('344', _('Mariabé'), '7', '45'),
  ('345', _('Oria Arriba'), '7', '45'),
  ('346', _('Pedasí'), '7', '45'),
  ('347', _('Purio'), '7', '45'),
  ('348', _('El Cañafístulo'), '7', '46'),
  ('349', _('Lajamina'), '7', '46'),
  ('350', _('Paraíso'), '7', '46'),
  ('351', _('Paritilla'), '7', '46'),
  ('352', _('Pocrí'), '7', '46'),
  ('353', _('Altos de Güera'), '7', '47'),
  ('354', _('Cambutal'), '7', '47'),
  ('355', _('Cañas'), '7', '47'),
  ('356', _('El Bebedero'), '7', '47'),
  ('357', _('El Cacao'), '7', '47'),
  ('358', _('El Cortezo'), '7', '47'),
  ('359', _('Flores'), '7', '47'),
  ('360', _('Guánico'), '7', '47'),
  ('361', _('Isla de Cañas'), '7', '47'),
  ('362', _('Tonosí'), '7', '47'),
  ('363', _('Tronosa'), '7', '47'),
  ('364', _('Boca de Balsa'), 'NB', '48'),
  ('365', _('Camarón Arriba'), 'NB', '48'),
  ('366', _('Cerro Banco'), 'NB', '48'),
  ('367', _('Cerro de Patena'), 'NB', '48'),
  ('368', _('Emplanada de Chorcha'), 'NB', '48'),
  ('369', _('Niba'), 'NB', '48'),
  ('370', _('Nämnoni'), 'NB', '48'),
  ('371', _('Soloy'), 'NB', '48'),
  ('372', _('Bisira'), 'NB', '49'),
  ('373', _('Bürí'), 'NB', '49'),
  ('374', _('Guariviara'), 'NB', '49'),
  ('375', _('Guoroni'), 'NB', '49'),
  ('376', _('Kankintú'), 'NB', '49'),
  ('377', _('Man Creek'), 'NB', '49'),
  ('378', _('Mününi'), 'NB', '49'),
  ('379', _('Piedra Roja'), 'NB', '49'),
  ('380', _('Tuwai'), 'NB', '49'),
  ('381', _('Bahía Azul'), 'NB', '50'),
  ('382', _('Calovébora o Santa Catalina'), 'NB', '50'),
  ('383', _('Kusapín'), 'NB', '50'),
  ('384', _('Loma Yuca'), 'NB', '50'),
  ('385', _('Río Chiriquí'), 'NB', '50'),
  ('386', _('Tobobe'), 'NB', '50'),
  ('387', _('Valle Bonito'), 'NB', '50'),
  ('388', _('Cascabel'), 'NB', '51'),
  ('389', _('Hato Corotú'), 'NB', '51'),
  ('390', _('Hato Culantro'), 'NB', '51'),
  ('391', _('Hato Jobo'), 'NB', '51'),
  ('392', _('Hato Julí'), 'NB', '51'),
  ('393', _('Hato Pilón'), 'NB', '51'),
  ('394', _('Quebrada de Loro'), 'NB', '51'),
  ('395', _('Salto Dupí'), 'NB', '51'),
  ('396', _('Alto Caballero'), 'NB', '52'),
  ('397', _('Bakama'), 'NB', '52'),
  ('398', _('Cerro Caña'), 'NB', '52'),
  ('399', _('Cerro Puerco'), 'NB', '52'),
  ('400', _('Chichica'), 'NB', '52'),
  ('401', _('Krüa'), 'NB', '52'),
  ('402', _('Maraca'), 'NB', '52'),
  ('403', _('Nibra'), 'NB', '52'),
  ('404', _('Peña Blanca'), 'NB', '52'),
  ('405', _('Roka'), 'NB', '52'),
  ('406', _('Sitio Prado'), 'NB', '52'),
  ('407', _('Umani'), 'NB', '52'),
  ('408', _('Cerro Iglesias'), 'NB', '53'),
  ('409', _('Hato Chamí'), 'NB', '53'),
  ('410', _('Jädaberi'), 'NB', '53'),
  ('411', _('Lajero'), 'NB', '53'),
  ('412', _('Susama'), 'NB', '53'),
  ('413', _('Agua de Salud'), 'NB', '54'),
  ('414', _('Alto de Jesús'), 'NB', '54'),
  ('415', _('Buenos Aires'), 'NB', '54'),
  ('416', _('Cerro Pelado'), 'NB', '54'),
  ('417', _('El Bale'), 'NB', '54'),
  ('418', _('El Paredón'), 'NB', '54'),
  ('419', _('El Piro'), 'NB', '54'),
  ('420', _('Guayabito'), 'NB', '54'),
  ('421', _('Güibale'), 'NB', '54'),
  ('422', _('Arraiján'), '8', '55'),
  ('423', _('Burunga'), '8', '55'),
  ('424', _('Cerro Silvestre'), '8', '55'),
  ('425', _('Juan Demóstenes Arosemena'), '8', '55'),
  ('426', _('Nuevo Emperador'), '8', '55'),
  ('427', _('Santa Clara'), '8', '55'),
  ('428', _('Veracruz'), '8', '55'),
  ('429', _('Vista Alegre'), '8', '55'),
  ('430', _('La Ensenada'), '8', '56'),
  ('431', _('La Esmeralda'), '8', '56'),
  ('432', _('La Guinea'), '8', '56'),
  ('433', _('Pedro González'), '8', '56'),
  ('434', _('Saboga'), '8', '56'),
  ('435', _('San Miguel'), '8', '56'),
  ('436', _('Caimito'), '8', '57'),
  ('437', _('Campana'), '8', '57'),
  ('438', _('Capira'), '8', '57'),
  ('439', _('Cermeño'), '8', '57'),
  ('440', _('Cirí Grande'), '8', '57'),
  ('441', _('Cirí de los Sotos'), '8', '57'),
  ('442', _('El Cacao'), '8', '57'),
  ('443', _('La Trinidad'), '8', '57'),
  ('444', _('Las Ollas Arriba'), '8', '57'),
  ('445', _('Lídice'), '8', '57'),
  ('446', _('Santa Rosa'), '8', '57'),
  ('447', _('Villa Carmen'), '8', '57'),
  ('448', _('Villa Rosario'), '8', '57'),
  ('449', _('Bejuco'), '8', '58'),
  ('450', _('Buenos Aires'), '8', '58'),
  ('451', _('Cabuya'), '8', '58'),
  ('452', _('Chame'), '8', '58'),
  ('453', _('Chicá'), '8', '58'),
  ('454', _('El Líbano'), '8', '58'),
  ('455', _('Las Lajas'), '8', '58'),
  ('456', _('Nueva Gorgona'), '8', '58'),
  ('457', _('Punta Chame'), '8', '58'),
  ('458', _('Sajalices'), '8', '58'),
  ('459', _('Sorá'), '8', '58'),
  ('460', _('Cañita'), '8', '59'),
  ('461', _('Chepillo'), '8', '59'),
  ('462', _('Chepo'), '8', '59'),
  ('463', _('Comarca Kuna de Madungandí'), '8', '59'),
  ('464', _('El Llano'), '8', '59'),
  ('465', _('Las Margaritas'), '8', '59'),
  ('466', _('Santa Cruz de Chinina'), '8', '59'),
  ('467', _('Tortí'), '8', '59'),
  ('468', _('Brujas'), '8', '60'),
  ('469', _('Chimán'), '8', '60'),
  ('470', _('Gonzalo Vásquez'), '8', '60'),
  ('471', _('Pásiga'), '8', '60'),
  ('472', _('Unión Santeña'), '8', '60'),
  ('473', _('Bella Vista'), '8', '61'),
  ('474', _('Betania'), '8', '61'),
  ('475', _('Curundú'), '8', '61'),
  ('476', _('El Chorrillo'), '8', '61'),
  ('477', _('Juan Díaz'), '8', '61'),
  ('478', _('La Exposición o Calidonia'), '8', '61'),
  ('479', _('Parque Lefevre'), '8', '61'),
  ('480', _('Pedregal'), '8', '61'),
  ('481', _('Pueblo Nuevo'), '8', '61'),
  ('482', _('Río Abajo'), '8', '61'),
  ('483', _('San Felipe'), '8', '61'),
  ('484', _('San Francisco'), '8', '61'),
  ('485', _('Santa Ana'), '8', '61'),
  ('486', _('Barrio Balboa'), '8', '62'),
  ('487', _('Barrio Colón'), '8', '62'),
  ('488', _('24 de Diciembre'), '8', '63'),
  ('489', _('Alcalde Díaz'), '8', '63'),
  ('490', _('Amador'), '8', '63'),
  ('491', _('Ancón'), '8', '63'),
  ('492', _('Arosemena'), '8', '63'),
  ('493', _('Chilibre'), '8', '63'),
  ('494', _('El Arado'), '8', '63'),
  ('495', _('El Coco'), '8', '63'),
  ('496', _('Ernesto Córdoba Campos'), '8', '63'),
  ('497', _('Feuillet'), '8', '63'),
  ('498', _('Guadalupe'), '8', '63'),
  ('499', _('Herrera'), '8', '63'),
  ('500', _('Hurtado'), '8', '63'),
  ('501', _('Iturralde'), '8', '63'),
  ('502', _('La Represa'), '8', '63'),
  ('503', _('Las Cumbres'), '8', '63'),
  ('504', _('Las Mañanitas'), '8', '63'),
  ('505', _('Los Díaz'), '8', '63'),
  ('506', _('Mendoza'), '8', '63'),
  ('507', _('Obaldía'), '8', '63'),
  ('508', _('Pacora'), '8', '63'),
  ('509', _('Playa Leona'), '8', '63'),
  ('510', _('Puerto Caimito'), '8', '63'),
  ('511', _('San Martín'), '8', '63'),
  ('512', _('Santa Rita'), '8', '63'),
  ('513', _('Tocumen'), '8', '63'),
  ('514', _('El Espino'), '8', '64'),
  ('515', _('El Higo'), '8', '64'),
  ('516', _('Guayabito'), '8', '64'),
  ('517', _('La Ermita'), '8', '64'),
  ('518', _('La Laguna'), '8', '64'),
  ('519', _('Las Uvas'), '8', '64'),
  ('520', _('Los Llanitos'), '8', '64'),
  ('521', _('San Carlos'), '8', '64'),
  ('522', _('San José'), '8', '64'),
  ('523', _('Amelia Denis de Icaza'), '8', '65'),
  ('524', _('Arnulfo Arias'), '8', '65'),
  ('525', _('Belisario Frías'), '8', '65'),
  ('526', _('Belisario Porras'), '8', '65'),
  ('527', _('José Domingo Espinar'), '8', '65'),
  ('528', _('Mateo Iturralde'), '8', '65'),
  ('529', _('Omar Torrijos'), '8', '65'),
  ('530', _('Rufina Alfaro'), '8', '65'),
  ('531', _('Victoriano Lorenzo'), '8', '65'),
  ('532', _('Otoque Occidente'), '8', '66'),
  ('533', _('Otoque Oriente'), '8', '66'),
  ('534', _('Taboga'), '8', '66'),
  ('535', _('Atalaya'), '9', '67'),
  ('536', _('El Barrito'), '9', '67'),
  ('537', _('La Carrillo'), '9', '67'),
  ('538', _('La Montañuela'), '9', '67'),
  ('539', _('San Antonio'), '9', '67'),
  ('540', _('Barnizal'), '9', '68'),
  ('541', _('Calobre'), '9', '68'),
  ('542', _('Chitra'), '9', '68'),
  ('543', _('El Cocla'), '9', '68'),
  ('544', _('El Potrero'), '9', '68'),
  ('545', _('La Laguna'), '9', '68'),
  ('546', _('La Raya de Calobre'), '9', '68'),
  ('547', _('La Tetilla'), '9', '68'),
  ('548', _('La Yeguada'), '9', '68'),
  ('549', _('Las Guías'), '9', '68'),
  ('550', _('Monjarás'), '9', '68'),
  ('551', _('San José'), '9', '68'),
  ('552', _('Cañazas'), '9', '69'),
  ('553', _('Cerro de Plata'), '9', '69'),
  ('554', _('El Aromillo'), '9', '69'),
  ('555', _('El Picador'), '9', '69'),
  ('556', _('Las Cruces'), '9', '69'),
  ('557', _('Los Valles'), '9', '69'),
  ('558', _('San José'), '9', '69'),
  ('559', _('San Marcelo'), '9', '69'),
  ('560', _('Bisvalles'), '9', '70'),
  ('561', _('Boró'), '9', '70'),
  ('562', _('La Mesa'), '9', '70'),
  ('563', _('Llano Grande'), '9', '70'),
  ('564', _('Los Milagros'), '9', '70'),
  ('565', _('San Bartolo'), '9', '70'),
  ('566', _('Cerro de Casa'), '9', '71'),
  ('567', _('Corozal'), '9', '71'),
  ('568', _('El María'), '9', '71'),
  ('569', _('El Prado'), '9', '71'),
  ('570', _('El Rincón'), '9', '71'),
  ('571', _('Las Palmas'), '9', '71'),
  ('572', _('Lolá'), '9', '71'),
  ('573', _('Pixvae'), '9', '71'),
  ('574', _('Puerto Vidal'), '9', '71'),
  ('575', _('San Martín de Porres'), '9', '71'),
  ('576', _('Viguí'), '9', '71'),
  ('577', _('Zapotillo'), '9', '71'),
  ('578', _('Arenas'), '9', '72'),
  ('579', _('El Cacao'), '9', '72'),
  ('580', _('Llano de Catival o Mariato'), '9', '72'),
  ('581', _('Quebro'), '9', '72'),
  ('582', _('Tebario'), '9', '72'),
  ('583', _('Costa Hermosa'), '9', '73'),
  ('584', _('Cébaco'), '9', '73'),
  ('585', _('Gobernadora'), '9', '73'),
  ('586', _('La Garceana'), '9', '73'),
  ('587', _('Leones'), '9', '73'),
  ('588', _('Montijo'), '9', '73'),
  ('589', _('Pilón'), '9', '73'),
  ('590', _('Unión del Norte'), '9', '73'),
  ('591', _('Catorce de Noviembre'), '9', '74'),
  ('592', _('Las Huacas'), '9', '74'),
  ('593', _('Los Castillos'), '9', '74'),
  ('594', _('Río de Jesús'), '9', '74'),
  ('595', _('Utira'), '9', '74'),
  ('596', _('Corral Falso'), '9', '75'),
  ('597', _('Los Hatillos'), '9', '75'),
  ('598', _('Remance'), '9', '75'),
  ('599', _('San Francisco'), '9', '75'),
  ('600', _('San José'), '9', '75'),
  ('601', _('San Juan'), '9', '75'),
  ('602', _('Calovébora'), '9', '76'),
  ('603', _('El Alto'), '9', '76'),
  ('604', _('El Cuay'), '9', '76'),
  ('605', _('El Pantano'), '9', '76'),
  ('606', _('Gatú o Gatucito'), '9', '76'),
  ('607', _('Rubén Cantú'), '9', '76'),
  ('608', _('Río Luis'), '9', '76'),
  ('609', _('Santa Fé'), '9', '76'),
  ('610', _('Canto del Llano'), '9', '77'),
  ('611', _('Carlos Santana Ávila'), '9', '77'),
  ('612', _('Edwin Fábrega'), '9', '77'),
  ('613', _('La Colorada'), '9', '77'),
  ('614', _('La Peña'), '9', '77'),
  ('615', _('La Raya de Santa María'), '9', '77'),
  ('616', _('Los Algarrobos'), '9', '77'),
  ('617', _('Ponuga'), '9', '77'),
  ('618', _('San Martín de Porres'), '9', '77'),
  ('619', _('San Pedro del Espino'), '9', '77'),
  ('620', _('Santiago'), '9', '77'),
  ('621', _('Urracá'), '9', '77'),
  ('622', _('Bahía Honda'), '9', '78'),
  ('623', _('Calidonia'), '9', '78'),
  ('624', _('Cativé'), '9', '78'),
  ('625', _('El Marañón'), '9', '78'),
  ('626', _('Guarumal'), '9', '78'),
  ('627', _('La Soledad'), '9', '78'),
  ('628', _('Quebrada de Oro'), '9', '78'),
  ('629', _('Rodeo Viejo'), '9', '78'),
  ('630', _('Río Grande'), '9', '78'),
  ('631', _('Soná'), '9', '78'),
)
