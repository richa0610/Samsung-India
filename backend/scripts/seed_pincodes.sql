-- ==============================================================================
-- Real-World India Post Pincode Seed Data
-- Target Database: tops_common_db (or mmtbtwob_tops)
-- Table: pincode
--
-- Rows are filled like the directory's own (user, 2026-10-16): updatedBy System, isRead Yes, one
-- token per import, status Approved, remarks Verified, securityDetails Secured, masterRemarks
-- Updated, and a PUI<id><pincode> ID. One pincode serves several post offices.
-- Run ONCE on a table without these rows - unlike scripts/seed_pincodes.py, this file does not
-- skip rows that are already there.
-- ==============================================================================

-- One token for this whole import, as the directory's own rows share theirs.
SET @token = FLOOR(10000 + RAND() * 90000);

INSERT INTO `pincode` (
  `pincodeUid`, `circleName`, `regionName`, `divisionName`, `officeName`,
  `pincode`, `officeType`, `delivery`, `district`, `stateName`,
  `latitude`, `longitude`,
  `updatedBy`, `updationOn`, `isRead`, `token`, `timestamp`, `status`, `remarks`, `securityDetails`, `masterRemarks`
) VALUES
-- Delhi
('PIN_110001_CP', 'Delhi Circle', 'Delhi Region', 'New Delhi Central Division', 'Connaught Place H.O', '110001', 'H.O', 'Delivery', 'NEW DELHI', 'DELHI', '28.6315', '77.2167', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110005_KB', 'Delhi Circle', 'Delhi Region', 'Central Division', 'Karol Bagh S.O', '110005', 'S.O', 'Delivery', 'CENTRAL DELHI', 'DELHI', '28.6517', '77.1906', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110019_NP', 'Delhi Circle', 'Delhi Region', 'South Division', 'Nehru Place S.O', '110019', 'S.O', 'Delivery', 'SOUTH DELHI', 'DELHI', '28.5494', '77.2522', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110021_CPY', 'Delhi Circle', 'Delhi Region', 'New Delhi South Division', 'Chanakyapuri S.O', '110021', 'S.O', 'Delivery', 'NEW DELHI', 'DELHI', '28.5921', '77.1856', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110075_DWK', 'Delhi Circle', 'Delhi Region', 'South West Division', 'Dwarka Sector 6 S.O', '110075', 'S.O', 'Delivery', 'SOUTH WEST DELHI', 'DELHI', '28.5794', '77.0655', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110085_ROH', 'Delhi Circle', 'Delhi Region', 'North West Division', 'Rohini Sector 7 S.O', '110085', 'S.O', 'Delivery', 'NORTH WEST DELHI', 'DELHI', '28.7112', '77.1189', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_110092_LXN', 'Delhi Circle', 'Delhi Region', 'East Division', 'Laxmi Nagar S.O', '110092', 'S.O', 'Delivery', 'EAST DELHI', 'DELHI', '28.6304', '77.2773', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Uttar Pradesh
('PIN_201301_NOI16', 'Uttar Pradesh Circle', 'Bareilly Region', 'Ghaziabad Division', 'Noida Sector 16 S.O', '201301', 'S.O', 'Delivery', 'GAUTAM BUDDHA NAGAR', 'UTTAR PRADESH', '28.5786', '77.3178', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_201309_NOI62', 'Uttar Pradesh Circle', 'Bareilly Region', 'Ghaziabad Division', 'Noida Sector 62 S.O', '201309', 'S.O', 'Delivery', 'NOIDA', 'UTTAR PRADESH', '28.6256', '77.3729', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_201310_GRNOI', 'Uttar Pradesh Circle', 'Bareilly Region', 'Ghaziabad Division', 'Greater Noida S.O', '201310', 'S.O', 'Delivery', 'GREATER NOIDA', 'UTTAR PRADESH', '28.4744', '77.5040', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_226001_LKO', 'Uttar Pradesh Circle', 'Lucknow HQ Region', 'Lucknow Division', 'Lucknow G.P.O.', '226001', 'G.P.O.', 'Delivery', 'LUCKNOW', 'UTTAR PRADESH', '26.8500', '80.9500', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_226010_GOMTI', 'Uttar Pradesh Circle', 'Lucknow HQ Region', 'Lucknow Division', 'Gomti Nagar S.O', '226010', 'S.O', 'Delivery', 'LUCKNOW', 'UTTAR PRADESH', '26.8667', '80.9982', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_201001_GZB', 'Uttar Pradesh Circle', 'Bareilly Region', 'Ghaziabad Division', 'Ghaziabad H.O', '201001', 'H.O', 'Delivery', 'GHAZIABAD', 'UTTAR PRADESH', '28.6692', '77.4538', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_208001_KNP', 'Uttar Pradesh Circle', 'Kanpur Region', 'Kanpur City Division', 'Kanpur H.O', '208001', 'H.O', 'Delivery', 'KANPUR NAGAR', 'UTTAR PRADESH', '26.4670', '80.3500', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_282001_AGR', 'Uttar Pradesh Circle', 'Agra Region', 'Agra Division', 'Agra Fort H.O', '282001', 'H.O', 'Delivery', 'AGRA', 'UTTAR PRADESH', '27.1800', '78.0200', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_221002_VNS', 'Uttar Pradesh Circle', 'Varanasi Region', 'Varanasi West Division', 'Varanasi Cantt H.O', '221002', 'H.O', 'Delivery', 'VARANASI', 'UTTAR PRADESH', '25.3333', '82.9833', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_211001_PRY', 'Uttar Pradesh Circle', 'Prayagraj Region', 'Allahabad Division', 'Prayagraj H.O', '211001', 'H.O', 'Delivery', 'PRAYAGRAJ', 'UTTAR PRADESH', '25.4358', '81.8463', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Haryana
('PIN_122001_GGN', 'Haryana Circle', 'Gurgaon Region', 'Gurgaon Division', 'Gurugram H.O', '122001', 'H.O', 'Delivery', 'GURUGRAM', 'HARYANA', '28.4595', '77.0266', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_122002_CYB', 'Haryana Circle', 'Gurgaon Region', 'Gurgaon Division', 'DLF Cyber City S.O', '122002', 'S.O', 'Delivery', 'GURUGRAM', 'HARYANA', '28.4947', '77.0889', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_122051_MNR', 'Haryana Circle', 'Gurgaon Region', 'Gurgaon Division', 'Manesar S.O', '122051', 'S.O', 'Delivery', 'GURUGRAM', 'HARYANA', '28.3548', '76.9388', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_121001_FBD1', 'Haryana Circle', 'Gurgaon Region', 'Faridabad Division', 'Faridabad NIT H.O', '121001', 'H.O', 'Delivery', 'FARIDABAD', 'HARYANA', '28.3870', '77.3070', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_121002_FBD16', 'Haryana Circle', 'Gurgaon Region', 'Faridabad Division', 'Faridabad Sector 16 S.O', '121002', 'S.O', 'Delivery', 'FARIDABAD', 'HARYANA', '28.4111', '77.3195', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_134109_PKL', 'Haryana Circle', 'Ambala HQ Region', 'Ambala Division', 'Panchkula Sector 8 S.O', '134109', 'S.O', 'Delivery', 'PANCHKULA', 'HARYANA', '30.6942', '76.8606', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_132001_KRN', 'Haryana Circle', 'Ambala HQ Region', 'Karnal Division', 'Karnal H.O', '132001', 'H.O', 'Delivery', 'KARNAL', 'HARYANA', '29.6857', '76.9905', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_133001_AMB', 'Haryana Circle', 'Ambala HQ Region', 'Ambala Division', 'Ambala Cantt H.O', '133001', 'H.O', 'Delivery', 'AMBALA', 'HARYANA', '30.3475', '76.8378', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Karnataka
('PIN_560001_BLR', 'Karnataka Circle', 'Bengaluru HQ Region', 'Bangalore GPO Division', 'Bengaluru G.P.O.', '560001', 'G.P.O.', 'Delivery', 'BENGALURU URBAN', 'KARNATAKA', '12.9800', '77.5925', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_560100_ECITY', 'Karnataka Circle', 'Bengaluru HQ Region', 'Bangalore South Division', 'Electronic City S.O', '560100', 'S.O', 'Delivery', 'BENGALURU URBAN', 'KARNATAKA', '12.8399', '77.6770', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_560066_WFD', 'Karnataka Circle', 'Bengaluru HQ Region', 'Bangalore East Division', 'Whitefield S.O', '560066', 'S.O', 'Delivery', 'BENGALURU URBAN', 'KARNATAKA', '12.9698', '77.7499', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_560034_KRM', 'Karnataka Circle', 'Bengaluru HQ Region', 'Bangalore South Division', 'Koramangala S.O', '560034', 'S.O', 'Delivery', 'BENGALURU URBAN', 'KARNATAKA', '12.9352', '77.6245', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_560002_BLRC', 'Karnataka Circle', 'Bengaluru HQ Region', 'Bangalore West Division', 'Bengaluru City S.O', '560002', 'S.O', 'Delivery', 'BENGALURU', 'KARNATAKA', '12.9644', '77.5770', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_570001_MYS', 'Karnataka Circle', 'South Karnataka Region', 'Mysore Division', 'Mysuru H.O', '570001', 'H.O', 'Delivery', 'MYSURU', 'KARNATAKA', '12.3051', '76.6554', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_575001_MLR', 'Karnataka Circle', 'South Karnataka Region', 'Mangalore Division', 'Mangaluru H.O', '575001', 'H.O', 'Delivery', 'DAKSHINA KANNADA', 'KARNATAKA', '12.8698', '74.8430', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_580020_HBL', 'Karnataka Circle', 'North Karnataka Region', 'Dharwad Division', 'Hubballi H.O', '580020', 'H.O', 'Delivery', 'DHARWAD', 'KARNATAKA', '15.3647', '75.1240', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Maharashtra
('PIN_400001_MUM', 'Maharashtra Circle', 'Mumbai Region', 'Mumbai GPO Division', 'Mumbai G.P.O.', '400001', 'G.P.O.', 'Delivery', 'MUMBAI', 'MAHARASHTRA', '18.9400', '72.8353', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400050_BND', 'Maharashtra Circle', 'Mumbai Region', 'Mumbai West Division', 'Bandra West S.O', '400050', 'S.O', 'Delivery', 'MUMBAI SUBURBAN', 'MAHARASHTRA', '19.0596', '72.8295', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400051_BKC', 'Maharashtra Circle', 'Mumbai Region', 'Mumbai West Division', 'Bandra Kurla Complex S.O', '400051', 'S.O', 'Delivery', 'MUMBAI SUBURBAN', 'MAHARASHTRA', '19.0664', '72.8665', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400069_AND', 'Maharashtra Circle', 'Mumbai Region', 'Mumbai West Division', 'Andheri East S.O', '400069', 'S.O', 'Delivery', 'MUMBAI SUBURBAN', 'MAHARASHTRA', '19.1136', '72.8697', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400076_POW', 'Maharashtra Circle', 'Mumbai Region', 'Mumbai East Division', 'Powai S.O', '400076', 'S.O', 'Delivery', 'MUMBAI SUBURBAN', 'MAHARASHTRA', '19.1176', '72.9060', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_411001_PUN', 'Maharashtra Circle', 'Pune Region', 'Pune City East Division', 'Pune H.O', '411001', 'H.O', 'Delivery', 'PUNE', 'MAHARASHTRA', '18.5204', '73.8567', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_411057_HINJ', 'Maharashtra Circle', 'Pune Region', 'Pune City West Division', 'Hinjawadi S.O', '411057', 'S.O', 'Delivery', 'PUNE', 'MAHARASHTRA', '18.5913', '73.7389', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_411014_VMN', 'Maharashtra Circle', 'Pune Region', 'Pune City East Division', 'Viman Nagar S.O', '411014', 'S.O', 'Delivery', 'PUNE', 'MAHARASHTRA', '18.5679', '73.9143', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400601_THN', 'Maharashtra Circle', 'Mumbai Region', 'Thane Division', 'Thane H.O', '400601', 'H.O', 'Delivery', 'THANE', 'MAHARASHTRA', '19.2183', '72.9781', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_400703_VSH', 'Maharashtra Circle', 'Mumbai Region', 'Navi Mumbai Division', 'Vashi S.O', '400703', 'S.O', 'Delivery', 'THANE', 'MAHARASHTRA', '19.0771', '72.9986', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_440001_NGP', 'Maharashtra Circle', 'Nagpur Region', 'Nagpur City Division', 'Nagpur G.P.O.', '440001', 'G.P.O.', 'Delivery', 'NAGPUR', 'MAHARASHTRA', '21.1458', '79.0882', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_422001_NSK', 'Maharashtra Circle', 'Nashik Region', 'Nashik Division', 'Nashik H.O', '422001', 'H.O', 'Delivery', 'NASHIK', 'MAHARASHTRA', '19.9975', '73.7898', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_431001_AUR', 'Maharashtra Circle', 'Aurangabad Region', 'Aurangabad Division', 'Aurangabad H.O', '431001', 'H.O', 'Delivery', 'AURANGABAD', 'MAHARASHTRA', '19.8762', '75.3433', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Telangana
('PIN_500001_HYD', 'Telangana Circle', 'Hyderabad City Region', 'Hyderabad GPO Division', 'Hyderabad G.P.O.', '500001', 'G.P.O.', 'Delivery', 'HYDERABAD', 'TELANGANA', '17.3850', '78.4867', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_500081_HITEC', 'Telangana Circle', 'Hyderabad City Region', 'Hyderabad South East Division', 'HITEC City S.O', '500081', 'S.O', 'Delivery', 'HYDERABAD', 'TELANGANA', '17.4474', '78.3762', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_500032_GCB', 'Telangana Circle', 'Hyderabad City Region', 'Secunderabad Division', 'Gachibowli S.O', '500032', 'S.O', 'Delivery', 'RANGAREDDY', 'TELANGANA', '17.4401', '78.3489', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_500034_BNJ', 'Telangana Circle', 'Hyderabad City Region', 'Hyderabad City Division', 'Banjara Hills S.O', '500034', 'S.O', 'Delivery', 'HYDERABAD', 'TELANGANA', '17.4156', '78.4352', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_500003_SEC', 'Telangana Circle', 'Hyderabad City Region', 'Secunderabad Division', 'Secunderabad H.O', '500003', 'H.O', 'Delivery', 'HYDERABAD', 'TELANGANA', '17.4399', '78.4983', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_506002_WGL', 'Telangana Circle', 'Hyderabad Region', 'Warangal Division', 'Warangal H.O', '506002', 'H.O', 'Delivery', 'WARANGAL', 'TELANGANA', '17.9784', '79.5941', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Tamil Nadu
('PIN_600001_CHN', 'Tamil Nadu Circle', 'Chennai City Region', 'Chennai GPO Division', 'Chennai G.P.O.', '600001', 'G.P.O.', 'Delivery', 'CHENNAI', 'TAMIL NADU', '13.0827', '80.2870', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_600017_TNG', 'Tamil Nadu Circle', 'Chennai City Region', 'Chennai Central Division', 'T Nagar S.O', '600017', 'S.O', 'Delivery', 'CHENNAI', 'TAMIL NADU', '13.0418', '80.2341', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_600096_OMR', 'Tamil Nadu Circle', 'Chennai City Region', 'Chennai South Division', 'Perungudi OMR S.O', '600096', 'S.O', 'Delivery', 'CHENNAI', 'TAMIL NADU', '12.9654', '80.2461', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_641001_CBE', 'Tamil Nadu Circle', 'Western Region', 'Coimbatore Division', 'Coimbatore H.O', '641001', 'H.O', 'Delivery', 'COIMBATORE', 'TAMIL NADU', '11.0168', '76.9558', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_625001_MDU', 'Tamil Nadu Circle', 'Southern Region', 'Madurai Division', 'Madurai H.O', '625001', 'H.O', 'Delivery', 'MADURAI', 'TAMIL NADU', '9.9252', '78.1198', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- West Bengal
('PIN_700001_KOL', 'West Bengal Circle', 'Kolkata Region', 'Kolkata GPO Division', 'Kolkata G.P.O.', '700001', 'G.P.O.', 'Delivery', 'KOLKATA', 'WEST BENGAL', '22.5726', '88.3639', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_700091_SLK', 'West Bengal Circle', 'Kolkata Region', 'Barasat Division', 'Salt Lake Sector V S.O', '700091', 'S.O', 'Delivery', 'NORTH 24 PARGANAS', 'WEST BENGAL', '22.5786', '88.4332', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_700156_NTW', 'West Bengal Circle', 'Kolkata Region', 'Barasat Division', 'New Town S.O', '700156', 'S.O', 'Delivery', 'NORTH 24 PARGANAS', 'WEST BENGAL', '22.5850', '88.4700', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_711101_HWR', 'West Bengal Circle', 'South Bengal Region', 'Howrah Division', 'Howrah H.O', '711101', 'H.O', 'Delivery', 'HOWRAH', 'WEST BENGAL', '22.5958', '88.2636', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_734001_SLG', 'West Bengal Circle', 'North Bengal Region', 'Darjeeling Division', 'Siliguri H.O', '734001', 'H.O', 'Delivery', 'DARJEELING', 'WEST BENGAL', '26.7271', '88.3953', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Gujarat
('PIN_380001_AMD', 'Gujarat Circle', 'Ahmedabad HQ Region', 'Ahmedabad City Division', 'Ahmedabad G.P.O.', '380001', 'G.P.O.', 'Delivery', 'AHMEDABAD', 'GUJARAT', '23.0225', '72.5714', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_380054_SGH', 'Gujarat Circle', 'Ahmedabad HQ Region', 'Ahmedabad City Division', 'SG Highway Thaltej S.O', '380054', 'S.O', 'Delivery', 'AHMEDABAD', 'GUJARAT', '23.0525', '72.5186', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_382016_GND', 'Gujarat Circle', 'Ahmedabad HQ Region', 'Gandhinagar Division', 'Gandhinagar Sector 16 S.O', '382016', 'S.O', 'Delivery', 'GANDHINAGAR', 'GUJARAT', '23.2324', '72.6514', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_395003_SRT', 'Gujarat Circle', 'Vadodara Region', 'Surat Division', 'Surat H.O', '395003', 'H.O', 'Delivery', 'SURAT', 'GUJARAT', '21.1702', '72.8311', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_390001_BRD', 'Gujarat Circle', 'Vadodara Region', 'Vadodara West Division', 'Vadodara H.O', '390001', 'H.O', 'Delivery', 'VADODARA', 'GUJARAT', '22.3072', '73.1812', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_360001_RJK', 'Gujarat Circle', 'Rajkot Region', 'Rajkot Division', 'Rajkot H.O', '360001', 'H.O', 'Delivery', 'RAJKOT', 'GUJARAT', '22.3039', '70.8022', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Rajasthan
('PIN_302001_JPR', 'Rajasthan Circle', 'Jaipur HQ Region', 'Jaipur City Division', 'Jaipur G.P.O.', '302001', 'G.P.O.', 'Delivery', 'JAIPUR', 'RAJASTHAN', '26.9124', '75.7873', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_302017_MLV', 'Rajasthan Circle', 'Jaipur HQ Region', 'Jaipur City Division', 'Malviya Nagar S.O', '302017', 'S.O', 'Delivery', 'JAIPUR', 'RAJASTHAN', '26.8532', '75.8166', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_302020_MNS', 'Rajasthan Circle', 'Jaipur HQ Region', 'Jaipur City Division', 'Mansarovar S.O', '302020', 'S.O', 'Delivery', 'JAIPUR', 'RAJASTHAN', '26.8628', '75.7618', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_342001_JDH', 'Rajasthan Circle', 'Western Region', 'Jodhpur Division', 'Jodhpur H.O', '342001', 'H.O', 'Delivery', 'JODHPUR', 'RAJASTHAN', '26.2389', '73.0243', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_313001_UDP', 'Rajasthan Circle', 'Southern Region', 'Udaipur Division', 'Udaipur H.O', '313001', 'H.O', 'Delivery', 'UDAIPUR', 'RAJASTHAN', '24.5854', '73.7125', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Kerala
('PIN_695001_TVM', 'Kerala Circle', 'Southern Region', 'Trivandrum North Division', 'Thiruvananthapuram G.P.O.', '695001', 'G.P.O.', 'Delivery', 'THIRUVANANTHAPURAM', 'KERALA', '8.5241', '76.9366', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_682001_KCH', 'Kerala Circle', 'Central Region', 'Ernakulam Division', 'Kochi S.O', '682001', 'S.O', 'Delivery', 'ERNAKULAM', 'KERALA', '9.9656', '76.2421', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_682042_INF', 'Kerala Circle', 'Central Region', 'Aluva Division', 'Infopark Kakkanad S.O', '682042', 'S.O', 'Delivery', 'ERNAKULAM', 'KERALA', '10.0125', '76.3582', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_673001_CLT', 'Kerala Circle', 'Northern Region', 'Calicut Division', 'Kozhikode H.O', '673001', 'H.O', 'Delivery', 'KOZHIKODE', 'KERALA', '11.2588', '75.7804', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Chandigarh
('PIN_160017_CHD17', 'Punjab Circle', 'Chandigarh Region', 'Chandigarh Division', 'Chandigarh Sector 17 G.P.O.', '160017', 'G.P.O.', 'Delivery', 'CHANDIGARH', 'CHANDIGARH', '30.7398', '76.7827', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_160035_CHD35', 'Punjab Circle', 'Chandigarh Region', 'Chandigarh Division', 'Chandigarh Sector 35 S.O', '160035', 'S.O', 'Delivery', 'CHANDIGARH', 'CHANDIGARH', '30.7259', '76.7645', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Madhya Pradesh
('PIN_462001_BHP', 'Madhya Pradesh Circle', 'Bhopal HQ Region', 'Bhopal Division', 'Bhopal G.P.O.', '462001', 'G.P.O.', 'Delivery', 'BHOPAL', 'MADHYA PRADESH', '23.2599', '77.4126', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_462011_MPN', 'Madhya Pradesh Circle', 'Bhopal HQ Region', 'Bhopal Division', 'M.P. Nagar S.O', '462011', 'S.O', 'Delivery', 'BHOPAL', 'MADHYA PRADESH', '23.2332', '77.4343', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_452001_IND', 'Madhya Pradesh Circle', 'Indore Region', 'Indore City Division', 'Indore G.P.O.', '452001', 'G.P.O.', 'Delivery', 'INDORE', 'MADHYA PRADESH', '22.7196', '75.8577', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_452010_VIJ', 'Madhya Pradesh Circle', 'Indore Region', 'Indore City Division', 'Vijay Nagar S.O', '452010', 'S.O', 'Delivery', 'INDORE', 'MADHYA PRADESH', '22.7533', '75.8937', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Bihar
('PIN_800001_PAT', 'Bihar Circle', 'Patna HQ Region', 'Patna Division', 'Patna G.P.O.', '800001', 'G.P.O.', 'Delivery', 'PATNA', 'BIHAR', '25.5941', '85.1376', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_800020_KNK', 'Bihar Circle', 'Patna HQ Region', 'Patna Division', 'Kankarbagh S.O', '800020', 'S.O', 'Delivery', 'PATNA', 'BIHAR', '25.5975', '85.1558', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_824101_AURBH', 'Bihar Circle', 'Patna HQ Region', 'Aurangabad Division', 'Aurangabad(BH) H.O', '824101', 'H.O', 'Delivery', 'AURANGABAD(BH)', 'BIHAR', '24.7500', '84.3700', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Punjab
('PIN_141001_LDH', 'Punjab Circle', 'Chandigarh Region', 'Ludhiana City Division', 'Ludhiana H.O', '141001', 'H.O', 'Delivery', 'LUDHIANA', 'PUNJAB', '30.9010', '75.8573', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_143001_ASR', 'Punjab Circle', 'Western Region', 'Amritsar Division', 'Amritsar G.P.O.', '143001', 'G.P.O.', 'Delivery', 'AMRITSAR', 'PUNJAB', '31.6340', '74.8723', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_160062_MOH', 'Punjab Circle', 'Chandigarh Region', 'Chandigarh Division', 'Mohali Phase 7 S.O', '160062', 'S.O', 'Delivery', 'SAHIBZADA AJIT SINGH NAGAR', 'PUNJAB', '30.7046', '76.7179', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Andhra Pradesh
('PIN_530001_VSK', 'Andhra Pradesh Circle', 'Visakhapatnam Region', 'Visakhapatnam Division', 'Visakhapatnam H.O', '530001', 'H.O', 'Delivery', 'VISAKHAPATNAM', 'ANDHRA PRADESH', '17.6868', '83.2185', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_520001_VJW', 'Andhra Pradesh Circle', 'Vijayawada Region', 'Vijayawada Division', 'Vijayawada H.O', '520001', 'H.O', 'Delivery', 'NTR', 'ANDHRA PRADESH', '16.5062', '80.6480', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Odisha
('PIN_751001_BBS', 'Odisha Circle', 'Bhubaneswar HQ Region', 'Bhubaneswar Division', 'Bhubaneswar G.P.O.', '751001', 'G.P.O.', 'Delivery', 'KHORDHA', 'ODISHA', '20.2961', '85.8245', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Assam
('PIN_781001_GWH', 'Assam Circle', 'Guwahati HQ Region', 'Guwahati Division', 'Guwahati G.P.O.', '781001', 'G.P.O.', 'Delivery', 'KAMRUP METROPOLITAN', 'ASSAM', '26.1856', '91.7500', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Jharkhand
('PIN_834001_RNC', 'Jharkhand Circle', 'Ranchi HQ Region', 'Ranchi Division', 'Ranchi G.P.O.', '834001', 'G.P.O.', 'Delivery', 'RANCHI', 'JHARKHAND', '23.3441', '85.3096', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Uttarakhand
('PIN_248001_DDN', 'Uttarakhand Circle', 'Dehradun HQ Region', 'Dehradun Division', 'Dehradun G.P.O.', '248001', 'G.P.O.', 'Delivery', 'DEHRADUN', 'UTTARAKHAND', '30.3165', '78.0322', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Goa
('PIN_403001_PNJ', 'Maharashtra Circle', 'Goa Region', 'Goa Division', 'Panaji H.O', '403001', 'H.O', 'Delivery', 'NORTH GOA', 'GOA', '15.4909', '73.8278', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_403601_MRG', 'Maharashtra Circle', 'Goa Region', 'Goa Division', 'Margao H.O', '403601', 'H.O', 'Delivery', 'SOUTH GOA', 'GOA', '15.2832', '73.9862', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),

-- Jammu and Kashmir
('PIN_180001_JMU', 'Jammu and Kashmir Circle', 'Srinagar HQ Region', 'Jammu Division', 'Jammu H.O', '180001', 'H.O', 'Delivery', 'JAMMU', 'JAMMU AND KASHMIR', '32.7266', '74.8570', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated'),
('PIN_190001_SXR', 'Jammu and Kashmir Circle', 'Srinagar HQ Region', 'Srinagar Division', 'Srinagar G.P.O.', '190001', 'G.P.O.', 'Delivery', 'SRINAGAR', 'JAMMU AND KASHMIR', '34.0837', '74.7973', 'System', NOW(), 'Yes', @token, NOW(), 'Approved', 'Verified', 'Secured', 'Updated')
;

-- Each new row's own ID, as the directory's rows have it: PUI + its id (at least 3 digits) + the
-- pincode, e.g. PUI016515571. The 'PIN_...' values above are stand-ins until the id is known.
UPDATE `pincode`
SET `pincodeUid` = CONCAT('PUI', LPAD(`id`, GREATEST(3, CHAR_LENGTH(`id`)), '0'), `pincode`)
WHERE `pincodeUid` LIKE 'PIN\_%';
