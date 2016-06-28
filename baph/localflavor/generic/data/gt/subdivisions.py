# encoding: utf8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('DEPARTMENTS', 'MUNICIPALITIES')

DEPARTMENTS = (
  ('AV', _('Alta Verapaz')),
  ('BV', _('Baja Verapaz')),
  ('CM', _('Chimaltenango')),
  ('CQ', _('Chiquimula')),
  ('PR', _('El Progreso')),
  ('ES', _('Escuintla')),
  ('GU', _('Guatemala')),
  ('HU', _('Huehuetenango')),
  ('IZ', _('Izabal')),
  ('JA', _('Jalapa')),
  ('JU', _('Jutiapa')),
  ('PE', _('Petén')),
  ('QZ', _('Quetzaltenango')),
  ('QC', _('Quiché')),
  ('RE', _('Retalhuleu')),
  ('SA', _('Sacatepéquez')),
  ('SM', _('San Marcos')),
  ('SR', _('Santa Rosa')),
  ('SO', _('Sololá')),
  ('SU', _('Suchitepéquez')),
  ('TO', _('Totonicapán')),
  ('ZA', _('Zacapa')),
)

MUNICIPALITIES = (
  ('1', _('Cahabón'), 'AV'),
  ('2', _('Chahal'), 'AV'),
  ('3', _('Chisec'), 'AV'),
  ('4', _('Cobán'), 'AV'),
  ('5', _('Fray Bartolomé de las Casas'), 'AV'),
  ('6', _('Lanquín'), 'AV'),
  ('7', _('Panzós'), 'AV'),
  ('8', _('Raxruha'), 'AV'),
  ('9', _('San Cristóbal Verapaz'), 'AV'),
  ('10', _('San Juan Chamelco'), 'AV'),
  ('11', _('San Pedro Carchá'), 'AV'),
  ('12', _('Santa Catarina La Tinta'), 'AV'),
  ('13', _('Santa Cruz Verapaz'), 'AV'),
  ('14', _('Senahú'), 'AV'),
  ('15', _('Tactic'), 'AV'),
  ('16', _('Tamahú'), 'AV'),
  ('17', _('Tucurú'), 'AV'),
  ('18', _('Cubulco'), 'BV'),
  ('19', _('Granados'), 'BV'),
  ('20', _('Purulhá'), 'BV'),
  ('21', _('Rabinal'), 'BV'),
  ('22', _('Salamá'), 'BV'),
  ('23', _('San Jerónimo'), 'BV'),
  ('24', _('San Miguel Chicaj'), 'BV'),
  ('25', _('Santa Cruz El Chol'), 'BV'),
  ('26', _('Acatenango'), 'CM'),
  ('27', _('Chimaltenango'), 'CM'),
  ('28', _('El Tejar'), 'CM'),
  ('29', _('Parramos'), 'CM'),
  ('30', _('Patzicía'), 'CM'),
  ('31', _('Patzún'), 'CM'),
  ('32', _('Pochuta'), 'CM'),
  ('33', _('San Andrés Itzapa'), 'CM'),
  ('34', _('San José Poaquil'), 'CM'),
  ('35', _('San Juan Comalapa'), 'CM'),
  ('36', _('San Martín Jilotepeque'), 'CM'),
  ('37', _('Santa Apolonia'), 'CM'),
  ('38', _('Santa Cruz Balanyá'), 'CM'),
  ('39', _('Tecpán Guatemala'), 'CM'),
  ('40', _('Yepocapa'), 'CM'),
  ('41', _('Zaragoza'), 'CM'),
  ('42', _('Camotán'), 'CQ'),
  ('43', _('Chiquimula'), 'CQ'),
  ('44', _('Concepción Las Minas'), 'CQ'),
  ('45', _('Esquipulas'), 'CQ'),
  ('46', _('Ipala'), 'CQ'),
  ('47', _('Jocotán'), 'CQ'),
  ('48', _('Olopa'), 'CQ'),
  ('49', _('Quezaltepeque'), 'CQ'),
  ('50', _('San Jacinto'), 'CQ'),
  ('51', _('San José La Arada'), 'CQ'),
  ('52', _('San Juan Ermita'), 'CQ'),
  ('53', _('El Jícaro'), 'PR'),
  ('54', _('Guastatoya'), 'PR'),
  ('55', _('Morazán'), 'PR'),
  ('56', _('San Agustín Acasaguastlán'), 'PR'),
  ('57', _('San Antonio La Paz'), 'PR'),
  ('58', _('San Cristóbal Acasaguastlán'), 'PR'),
  ('59', _('Sanarate'), 'PR'),
  ('60', _('Sansare'), 'PR'),
  ('61', _('Escuintla'), 'ES'),
  ('62', _('Guanagazapa'), 'ES'),
  ('63', _('Iztapa'), 'ES'),
  ('64', _('La Democracia'), 'ES'),
  ('65', _('La Gomera'), 'ES'),
  ('66', _('Masagua'), 'ES'),
  ('67', _('Nueva Concepción'), 'ES'),
  ('68', _('Palín'), 'ES'),
  ('69', _('San José'), 'ES'),
  ('70', _('San Vicente Pacaya'), 'ES'),
  ('71', _('Santa Lucía Cotzumalguapa'), 'ES'),
  ('72', _('Siquinalá'), 'ES'),
  ('73', _('Tiquisate'), 'ES'),
  ('74', _('Amatitlán'), 'GU'),
  ('75', _('Chinautla'), 'GU'),
  ('76', _('Chuarrancho'), 'GU'),
  ('77', _('Fraijanes'), 'GU'),
  ('78', _('Guatemala City'), 'GU'),
  ('79', _('Mixco'), 'GU'),
  ('80', _('Palencia'), 'GU'),
  ('81', _('Petapa'), 'GU'),
  ('82', _('San José Pinula'), 'GU'),
  ('83', _('San José del Golfo'), 'GU'),
  ('84', _('San Juan Sacatepéquez'), 'GU'),
  ('85', _('San Pedro Ayampuc'), 'GU'),
  ('86', _('San Pedro Sacatepéquez'), 'GU'),
  ('87', _('San Raymundo'), 'GU'),
  ('88', _('Santa Catarina Pinula'), 'GU'),
  ('89', _('Villa Canales'), 'GU'),
  ('90', _('Villa Nueva'), 'GU'),
  ('91', _('Aguacatán'), 'HU'),
  ('92', _('Chiantla'), 'HU'),
  ('93', _('Colotenango'), 'HU'),
  ('94', _('Concepción Huista'), 'HU'),
  ('95', _('Cuilco'), 'HU'),
  ('96', _('Huehuetenango'), 'HU'),
  ('97', _('Ixtahuacán'), 'HU'),
  ('98', _('Jacaltenango'), 'HU'),
  ('99', _('La Democracia'), 'HU'),
  ('100', _('La Libertad'), 'HU'),
  ('101', _('La Unión Cantinil'), 'HU'),
  ('102', _('Malacatancito'), 'HU'),
  ('103', _('Nentón'), 'HU'),
  ('104', _('San Antonio Huista'), 'HU'),
  ('105', _('San Gaspar Ixchil'), 'HU'),
  ('106', _('San Juan Atitán'), 'HU'),
  ('107', _('San Juan Ixcoy'), 'HU'),
  ('108', _('San Mateo Ixtatán'), 'HU'),
  ('109', _('San Miguel Acatán'), 'HU'),
  ('110', _('San Pedro Necta'), 'HU'),
  ('111', _('San Rafael La Independencia'), 'HU'),
  ('112', _('San Rafael Petzal'), 'HU'),
  ('113', _('San Sebastián Coatán'), 'HU'),
  ('114', _('San Sebastián Huehuetenango'), 'HU'),
  ('115', _('Santa Ana Huista'), 'HU'),
  ('116', _('Santa Bárbara'), 'HU'),
  ('117', _('Santa Cruz Barillas'), 'HU'),
  ('118', _('Santa Eulalia'), 'HU'),
  ('119', _('Santiago Chimaltenango'), 'HU'),
  ('120', _('Soloma'), 'HU'),
  ('121', _('Tectitán'), 'HU'),
  ('122', _('Todos Santos Cuchumatan'), 'HU'),
  ('123', _('El Estor'), 'IZ'),
  ('124', _('Livingston'), 'IZ'),
  ('125', _('Los Amates'), 'IZ'),
  ('126', _('Morales'), 'IZ'),
  ('127', _('Puerto Barrios'), 'IZ'),
  ('128', _('Jalapa'), 'JA'),
  ('129', _('Mataquescuintla'), 'JA'),
  ('130', _('Monjas'), 'JA'),
  ('131', _('San Carlos Alzatate'), 'JA'),
  ('132', _('San Luis Jilotepeque'), 'JA'),
  ('133', _('San Manuel Chaparrón'), 'JA'),
  ('134', _('San Pedro Pinula'), 'JA'),
  ('135', _('Agua Blanca'), 'JU'),
  ('136', _('Asunción Mita'), 'JU'),
  ('137', _('Atescatempa'), 'JU'),
  ('138', _('Comapa'), 'JU'),
  ('139', _('Conguaco'), 'JU'),
  ('140', _('El Adelanto'), 'JU'),
  ('141', _('El Progreso'), 'JU'),
  ('142', _('Jalpatagua'), 'JU'),
  ('143', _('Jerez'), 'JU'),
  ('144', _('Jutiapa'), 'JU'),
  ('145', _('Moyuta'), 'JU'),
  ('146', _('Pasaco'), 'JU'),
  ('147', _('Quesada'), 'JU'),
  ('148', _('San José Acatempa'), 'JU'),
  ('149', _('Santa Catarina Mita'), 'JU'),
  ('150', _('Yupiltepeque'), 'JU'),
  ('151', _('Zapotitlán'), 'JU'),
  ('152', _('Dolores'), 'PE'),
  ('153', _('Flores'), 'PE'),
  ('154', _('La Libertad'), 'PE'),
  ('155', _('Las Cruces'), 'PE'),
  ('156', _('Melchor de Mencos'), 'PE'),
  ('157', _('Poptún'), 'PE'),
  ('158', _('San Andrés'), 'PE'),
  ('159', _('San Benito'), 'PE'),
  ('160', _('San Francisco'), 'PE'),
  ('161', _('San José'), 'PE'),
  ('162', _('San Luis'), 'PE'),
  ('163', _('Santa Ana'), 'PE'),
  ('164', _('Sayaxché'), 'PE'),
  ('165', _('Almolonga'), 'QZ'),
  ('166', _('Cabricán'), 'QZ'),
  ('167', _('Cajolá'), 'QZ'),
  ('168', _('Cantel'), 'QZ'),
  ('169', _('Coatepeque'), 'QZ'),
  ('170', _('Colomba'), 'QZ'),
  ('171', _('Concepción Chiquirichapa'), 'QZ'),
  ('172', _('El Palmar'), 'QZ'),
  ('173', _('Flores Costa Cuca'), 'QZ'),
  ('174', _('Génova'), 'QZ'),
  ('175', _('Huitán'), 'QZ'),
  ('176', _('La Esperanza'), 'QZ'),
  ('177', _('Olintepeque'), 'QZ'),
  ('178', _('Ostuncalco'), 'QZ'),
  ('179', _('Palestina de Los Altos'), 'QZ'),
  ('180', _('Quetzaltenango'), 'QZ'),
  ('181', _('Salcajá'), 'QZ'),
  ('182', _('San Carlos Sija'), 'QZ'),
  ('183', _('San Francisco La Unión'), 'QZ'),
  ('184', _('San Martín Sacatepéquez'), 'QZ'),
  ('185', _('San Mateo'), 'QZ'),
  ('186', _('San Miguel Sigüilá'), 'QZ'),
  ('187', _('Sibilia'), 'QZ'),
  ('188', _('Zunil'), 'QZ'),
  ('189', _('Canillá'), 'QC'),
  ('190', _('Chajul'), 'QC'),
  ('191', _('Chicamán'), 'QC'),
  ('192', _('Chichicastenango'), 'QC'),
  ('193', _('Chiché'), 'QC'),
  ('194', _('Chinique'), 'QC'),
  ('195', _('Cunén'), 'QC'),
  ('196', _('Ixcán'), 'QC'),
  ('197', _('Joyabaj'), 'QC'),
  ('198', _('Nebaj'), 'QC'),
  ('199', _('Pachalum'), 'QC'),
  ('200', _('Patzité'), 'QC'),
  ('201', _('Sacapulas'), 'QC'),
  ('202', _('San Andrés Sajcabajá'), 'QC'),
  ('203', _('San Antonio Ilotenango'), 'QC'),
  ('204', _('San Bartolomé Jocotenango'), 'QC'),
  ('205', _('San Juan Cotzal'), 'QC'),
  ('206', _('San Pedro Jocopilas'), 'QC'),
  ('207', _('Santa Cruz del Quiché'), 'QC'),
  ('208', _('Uspantán'), 'QC'),
  ('209', _('Zacualpa'), 'QC'),
  ('210', _('Champerico'), 'RE'),
  ('211', _('El Asintal'), 'RE'),
  ('212', _('Nuevo San Carlos'), 'RE'),
  ('213', _('Retalhuleu'), 'RE'),
  ('214', _('San Andrés Villa Seca'), 'RE'),
  ('215', _('San Felipe'), 'RE'),
  ('216', _('San Martín Zapotitlán'), 'RE'),
  ('217', _('San Sebastián'), 'RE'),
  ('218', _('Santa Cruz Muluá'), 'RE'),
  ('219', _('Alotenango'), 'SA'),
  ('220', _('Antigua'), 'SA'),
  ('221', _('Ciudad Vieja'), 'SA'),
  ('222', _('Jocotenango'), 'SA'),
  ('223', _('Magdalena Milpas Altas'), 'SA'),
  ('224', _('Pastores'), 'SA'),
  ('225', _('San Antonio Aguas Calientes'), 'SA'),
  ('226', _('San Bartolomé Milpas Altas'), 'SA'),
  ('227', _('San Lucas Sacatepéquez'), 'SA'),
  ('228', _('San Miguel Dueñas'), 'SA'),
  ('229', _('Santa Catarina Barahona'), 'SA'),
  ('230', _('Santa Lucía Milpas Altas'), 'SA'),
  ('231', _('Santa María de Jesús'), 'SA'),
  ('232', _('Santiago Sacatepéquez'), 'SA'),
  ('233', _('Santo Domingo Xenacoj'), 'SA'),
  ('234', _('Sumpango'), 'SA'),
  ('235', _('Ayutla'), 'SM'),
  ('236', _('Catarina'), 'SM'),
  ('237', _('Comitancillo'), 'SM'),
  ('238', _('Concepción Tutuapa'), 'SM'),
  ('239', _('El Quetzal'), 'SM'),
  ('240', _('El Rodeo'), 'SM'),
  ('241', _('El Tumbador'), 'SM'),
  ('242', _('Esquipulas Palo Gordo'), 'SM'),
  ('243', _('Ixchiguan'), 'SM'),
  ('244', _('La Reforma'), 'SM'),
  ('245', _('Malacatán'), 'SM'),
  ('246', _('Nuevo Progreso'), 'SM'),
  ('247', _('Ocos'), 'SM'),
  ('248', _('Pajapita'), 'SM'),
  ('249', _('Río Blanco'), 'SM'),
  ('250', _('San Antonio Sacatepéquez'), 'SM'),
  ('251', _('San Cristóbal Cucho'), 'SM'),
  ('252', _('San José Ojetenam'), 'SM'),
  ('253', _('San Lorenzo'), 'SM'),
  ('254', _('San Marcos'), 'SM'),
  ('255', _('San Miguel Ixtahuacán'), 'SM'),
  ('256', _('San Pablo'), 'SM'),
  ('257', _('San Pedro Sacatepéquez'), 'SM'),
  ('258', _('San Rafael Pie de La Cuesta'), 'SM'),
  ('259', _('San Sibinal'), 'SM'),
  ('260', _('Sipacapa'), 'SM'),
  ('261', _('Tacaná'), 'SM'),
  ('262', _('Tajumulco'), 'SM'),
  ('263', _('Tejutla'), 'SM'),
  ('264', _('Barberena'), 'SR'),
  ('265', _('Casillas'), 'SR'),
  ('266', _('Chiquimulilla'), 'SR'),
  ('267', _('Cuilapa'), 'SR'),
  ('268', _('Guazacapán'), 'SR'),
  ('269', _('Nueva Santa Rosa'), 'SR'),
  ('270', _('Oratorio'), 'SR'),
  ('271', _('Pueblo Nuevo Viñas'), 'SR'),
  ('272', _('San Juan Tecuaco'), 'SR'),
  ('273', _('San Rafael Las Flores'), 'SR'),
  ('274', _('Santa Cruz Naranjo'), 'SR'),
  ('275', _('Santa María Ixhuatán'), 'SR'),
  ('276', _('Santa Rosa de Lima'), 'SR'),
  ('277', _('Taxisco'), 'SR'),
  ('278', _('Concepción'), 'SO'),
  ('279', _('Nahualá'), 'SO'),
  ('280', _('Panajachel'), 'SO'),
  ('281', _('San Andrés Semetabaj'), 'SO'),
  ('282', _('San Antonio Palopó'), 'SO'),
  ('283', _('San José Chacaya'), 'SO'),
  ('284', _('San Juan La Laguna'), 'SO'),
  ('285', _('San Lucas Tolimán'), 'SO'),
  ('286', _('San Marcos La Laguna'), 'SO'),
  ('287', _('San Pablo La Laguna'), 'SO'),
  ('288', _('San Pedro La Laguna'), 'SO'),
  ('289', _('Santa Catarina Ixtahuacan'), 'SO'),
  ('290', _('Santa Catarina Palopó'), 'SO'),
  ('291', _('Santa Clara La Laguna'), 'SO'),
  ('292', _('Santa Cruz La Laguna'), 'SO'),
  ('293', _('Santa Lucía Utatlán'), 'SO'),
  ('294', _('Santa María Visitación'), 'SO'),
  ('295', _('Santiago Atitlán'), 'SO'),
  ('296', _('Sololá'), 'SO'),
  ('297', _('Chicacao'), 'SU'),
  ('298', _('Cuyotenango'), 'SU'),
  ('299', _('Mazatenango'), 'SU'),
  ('300', _('Patulul'), 'SU'),
  ('301', _('Pueblo Nuevo'), 'SU'),
  ('302', _('Río Bravo'), 'SU'),
  ('303', _('Samayac'), 'SU'),
  ('304', _('San Antonio Suchitepéquez'), 'SU'),
  ('305', _('San Bernardino'), 'SU'),
  ('306', _('San Francisco Zapotitlán'), 'SU'),
  ('307', _('San Gabriel'), 'SU'),
  ('308', _('San José El Idolo'), 'SU'),
  ('309', _('San Juan Bautista'), 'SU'),
  ('310', _('San Lorenzo'), 'SU'),
  ('311', _('San Miguel Panán'), 'SU'),
  ('312', _('San Pablo Jocopilas'), 'SU'),
  ('313', _('Santa Bárbara'), 'SU'),
  ('314', _('Santo Domingo Suchitepequez'), 'SU'),
  ('315', _('Santo Tomas La Unión'), 'SU'),
  ('316', _('Zunilito'), 'SU'),
  ('317', _('Momostenango'), 'TO'),
  ('318', _('San Andrés Xecul'), 'TO'),
  ('319', _('San Bartolo'), 'TO'),
  ('320', _('San Cristóbal Totonicapán'), 'TO'),
  ('321', _('San Francisco El Alto'), 'TO'),
  ('322', _('Santa Lucía La Reforma'), 'TO'),
  ('323', _('Santa María Chiquimula'), 'TO'),
  ('324', _('Totonicapán'), 'TO'),
  ('325', _('Cabañas'), 'ZA'),
  ('326', _('Estanzuela'), 'ZA'),
  ('327', _('Gualán'), 'ZA'),
  ('328', _('Huité'), 'ZA'),
  ('329', _('La Unión'), 'ZA'),
  ('330', _('Río Hondo'), 'ZA'),
  ('331', _('San Diego'), 'ZA'),
  ('332', _('Teculután'), 'ZA'),
  ('333', _('Usumatlán'), 'ZA'),
  ('334', _('Zacapa'), 'ZA'),
)
