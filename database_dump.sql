-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 24, 2026 at 11:41 AM
-- Server version: 8.0.46
-- PHP Version: 8.4.23

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mmtbtwob_tops`
--

-- --------------------------------------------------------

--
-- Table structure for table `accounts`
--

CREATE TABLE `accounts` (
  `id` int NOT NULL,
  `accountsUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venuePhone` bigint DEFAULT NULL,
  `venueAddress` mediumtext COLLATE utf8mb4_general_ci,
  `contactPersonName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `contactPersonPhone` bigint DEFAULT NULL,
  `zoneHeadName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zoneHeadEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zoneHeadPhone` bigint DEFAULT NULL,
  `trainerEmployeeId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerPhone` bigint DEFAULT NULL,
  `trainingUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainingDate` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainingHub` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `batchSize` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `confirmedPax` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tariff` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tax` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `total` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `totalPaid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dueAmount` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `referenceNumber` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dateOfPayment` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dateOfAttendence` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `attendenceSheet` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueBill` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hotelRemarks` longtext COLLATE utf8mb4_general_ci,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int NOT NULL,
  `adminUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `altPhone` bigint DEFAULT NULL,
  `gender` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dob` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `fatherName` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `motherName` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localCity` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localDistrict` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localState` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localPinCode` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localLandmark` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentCity` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentDistrict` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentState` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentPinCode` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentLandmark` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aadharNo` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aadharImage` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `profilePhoto` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `about` longtext COLLATE utf8mb4_general_ci,
  `resume` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `otherDocument` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `facebook` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://facebook.com/',
  `twitter` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://twitter.com/',
  `instagram` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://instagram.com/',
  `linkedin` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.linkedin.com/company/',
  `youtube` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.youtube.com/',
  `github` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobStatus` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `joinedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `company` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `band` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reportingManager` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `postedIn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `role` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'NA',
  `access` longtext COLLATE utf8mb4_general_ci,
  `designation` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `salary` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `companyEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `visitingCard` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `idCard` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `offerLetter` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `letterHead` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `promoCode` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ;

-- --------------------------------------------------------

--
-- Table structure for table `advertising`
--

CREATE TABLE `advertising` (
  `id` int NOT NULL,
  `advertisingUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `agencyUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `adsType` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `actionButtonText` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `actionButtonTarget` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `blueTick` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `title` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `summary` mediumtext COLLATE utf8mb4_general_ci,
  `image` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `thumbnails` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `video` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `promoCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `expiredOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `postingDate` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `isRead` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `visibleOnWeb` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `agency`
--

CREATE TABLE `agency` (
  `id` int NOT NULL,
  `agencyUid` char(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `companyName` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `website` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logo` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `authenticationDocs` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `certificateNo` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localCity` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localDistrict` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localState` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localPinCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localLandmark` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentCity` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentDistrict` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentState` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentPinCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentLandmark` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `approvedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `managementFee` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aboutAgency` longtext COLLATE utf8mb4_general_ci,
  `facebook` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://facebook.com/',
  `twitter` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://twitter.com/',
  `instagram` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://instagram.com/',
  `linkedin` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.linkedin.com/company/',
  `youtube` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.youtube.com/',
  `isRead` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `contractExpired` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Not Expired',
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `agencyteam`
--

CREATE TABLE `agencyteam` (
  `id` int NOT NULL,
  `agencyTeamUid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `companyUid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `company` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `altPhone` bigint DEFAULT NULL,
  `officialEmail` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dob` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `gender` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `offerId` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `designation` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `role` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobCity` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobState` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobPincode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `profilePhoto` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'defaultfile.png',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '$2y$10$qDSaaJA.3/PPItCLB2xdt.xFZaGa7IfHLhCq.EQGILTEZzaj3wRju',
  `filePath` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `securityDetails` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `assessment`
--

CREATE TABLE `assessment` (
  `id` int NOT NULL,
  `assessmentUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `assessmentSuiteUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `traineeUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `questionId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `selectedOption` longtext COLLATE utf8mb4_general_ci,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Approved',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `assessmentsuite`
--

CREATE TABLE `assessmentsuite` (
  `id` int NOT NULL,
  `assessmentSuiteUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `courseUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `courseName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `examTitle` mediumtext COLLATE utf8mb4_general_ci,
  `description` longtext COLLATE utf8mb4_general_ci,
  `assessment_type` varchar(50) COLLATE utf8mb4_general_ci DEFAULT 'Quiz',
  `settings` longtext COLLATE utf8mb4_general_ci COMMENT 'Stores Global Quiz Settings (Shuffle, Progress Bar, etc.)',
  `theme` longtext COLLATE utf8mb4_general_ci COMMENT 'Stores Theme Colors, Fonts, Backgrounds',
  `noOfQuestion` int DEFAULT '0',
  `testTime` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `assessment_results`
--

CREATE TABLE `assessment_results` (
  `id` int NOT NULL,
  `resultUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `traineeUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `assessmentSuiteUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `attemptNumber` int DEFAULT '1' COMMENT '1st try, 2nd try, etc.',
  `totalScore` decimal(10,2) DEFAULT '0.00',
  `maxScore` decimal(10,2) DEFAULT '0.00',
  `percentage` decimal(5,2) DEFAULT '0.00',
  `startedAt` datetime DEFAULT NULL,
  `submittedAt` datetime DEFAULT NULL,
  `durationSeconds` int DEFAULT '0' COMMENT 'Time taken in seconds',
  `status` varchar(20) COLLATE utf8mb4_general_ci DEFAULT 'Started' COMMENT 'Started, Submitted, Timeout',
  `answersSnapshot` longtext COLLATE utf8mb4_general_ci COMMENT 'JSON dump of all answers for quick viewing',
  `ipAddress` varchar(45) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `deviceInfo` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `attendance`
--

CREATE TABLE `attendance` (
  `id` int NOT NULL,
  `attendanceUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `traineeUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `markedOn` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `checkInPhoto` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `checkOutPhoto` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `checkOutTime` datetime DEFAULT NULL,
  `checkInDistance` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'E.g., 45 meters',
  `geofenceBypass` tinyint(1) DEFAULT '0' COMMENT '1=Bypassed by Trainer',
  `bypassRemark` text COLLATE utf8mb4_general_ci,
  `attemptCount` int DEFAULT '1',
  `isTheftLocked` tinyint(1) DEFAULT '0' COMMENT '0=Unlocked, 1=Locked',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `sessionMeta` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci,
  `theftAttemptsLeft` int DEFAULT '3' COMMENT 'Countdown from 3 to 0',
  `theftRemarks` longtext COLLATE utf8mb4_general_ci COMMENT 'Log of tab switches'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `attendance_logs`
--

CREATE TABLE `attendance_logs` (
  `id` int NOT NULL,
  `logUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `traineeUid` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `moduleId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `markedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) COLLATE utf8mb4_general_ci DEFAULT 'Present',
  `ipAddress` varchar(45) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `deviceInfo` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `locationData` text COLLATE utf8mb4_general_ci COMMENT 'Lat,Long if GeoFencing on'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `blogs`
--

CREATE TABLE `blogs` (
  `id` int NOT NULL,
  `blogsUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `title` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `summary` longtext COLLATE utf8mb4_general_ci,
  `tags` mediumtext COLLATE utf8mb4_general_ci,
  `description` longtext COLLATE utf8mb4_general_ci,
  `image` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `thumbnails` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `video` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `onTranding` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `trandingTill` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '00/00/00',
  `latest` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `newsFlash` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `featuredStories` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `isRead` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `booking`
--

CREATE TABLE `booking` (
  `id` int NOT NULL,
  `bookingUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zone` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `region` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `checkIn` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `checkOut` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `venueName` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueAddress` longtext COLLATE utf8mb4_general_ci,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tariff` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tax` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `total` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `totalPaid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dueAmount` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `referenceNumber` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dateOfPayment` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueBill` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hotelRemarks` mediumtext COLLATE utf8mb4_general_ci,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `career`
--

CREATE TABLE `career` (
  `id` int NOT NULL,
  `careerUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `altPhone` bigint DEFAULT NULL,
  `gender` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dob` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `fatherName` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `motherName` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `expertisedIn` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `currPostion` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `yearsOfExperience` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `intrestedField` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localCity` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localDistrict` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localState` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localPinCode` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `localLandmark` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentCity` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentDistrict` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentState` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentPinCode` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permanentLandmark` varchar(180) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aadharNo` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aadharImage` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `profilePhoto` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `coverLetter` longtext COLLATE utf8mb4_general_ci,
  `resume` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `otherDocument` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `about` longtext COLLATE utf8mb4_general_ci,
  `role` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'NA',
  `facebook` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://facebook.com/',
  `twitter` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://twitter.com/',
  `instagram` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://instagram.com/',
  `linkedin` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.linkedin.com/company/',
  `youtube` varchar(300) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://www.youtube.com/',
  `promoCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `id` int NOT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `description` longtext COLLATE utf8mb4_general_ci,
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `companydetails`
--

CREATE TABLE `companydetails` (
  `id` int NOT NULL,
  `companyUid` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ownerName` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `shortName` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `companyName` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `registrationDate` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `registrationNumber` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cin` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `moa` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `aoa` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `udyamNumber` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `panNumber` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bankName` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `accountNo` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ifscCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `micrCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `accountHolderName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bankAddress` mediumtext COLLATE utf8mb4_general_ci,
  `upi` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `qrCode` varchar(400) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `websiteUrl` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaLogo` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logo` varchar(400) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `feviconpng` varchar(400) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `feviconico` varchar(400) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `companyMobNo` bigint DEFAULT NULL,
  `companyEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `street` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `district` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pinCode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `landmark` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `maplink` varchar(400) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `facebook` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `instagram` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `youtube` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `twitter` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `whatsaap` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `googleTag` longtext COLLATE utf8mb4_general_ci,
  `gtagjs` longtext COLLATE utf8mb4_general_ci,
  `siteVerificationGoogle` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `siteVerificationfacebook` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `facebookPageId` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `captchaCode` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaKeywords` mediumtext COLLATE utf8mb4_general_ci,
  `metaDescription` mediumtext COLLATE utf8mb4_general_ci,
  `metaSubject` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaCopyright` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaLanguage` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaRevised` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaAbstract` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaTopic` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaSummary` mediumtext COLLATE utf8mb4_general_ci,
  `metaClassification` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metaTagline` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `chatBotScript` longtext COLLATE utf8mb4_general_ci,
  `removeBrandingTawk` longtext COLLATE utf8mb4_general_ci,
  `disableInspact` longtext COLLATE utf8mb4_general_ci,
  `latitude` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `longitude` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pageRefresh` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '600',
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `conference`
--

CREATE TABLE `conference` (
  `id` int NOT NULL,
  `conferenceUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zone` varchar(120) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `region` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `company` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `requestedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerEmployeeId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceType` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Non Residential Conference',
  `conferenceDate` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceEndsOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceTime` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceStatus` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Scheduled',
  `activeModuleId` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `liveQuizState` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'IDLE' COMMENT 'IDLE, WAITING, QUESTION_LIVE, LEADERBOARD, FINISHED',
  `liveQuestionId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Stores the UID of the active question',
  `liveTimerEndsAt` bigint DEFAULT '0',
  `actualStartedAt` datetime DEFAULT NULL,
  `actualEndedAt` datetime DEFAULT NULL,
  `enableCheckIn` tinyint(1) DEFAULT '0' COMMENT '1=Enabled, 0=Disabled',
  `trainingHub` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `audience` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sessionType` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainingType` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `batchSize` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `confirmedPax` varchar(150) COLLATE utf8mb4_general_ci DEFAULT '0',
  `attendanceSheetPax` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '0',
  `state` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `district` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `venueUid` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `geoLatitude` decimal(10,8) DEFAULT NULL,
  `geoLongitude` decimal(11,8) DEFAULT NULL,
  `geoRadius` int DEFAULT '100' COMMENT 'Radius in meters',
  `assessmentFor` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `suiteTitle` mediumtext COLLATE utf8mb4_general_ci,
  `preAssessmentUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Stores UID for Pre-Test',
  `postAssessmentUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Stores UID for Post-Test',
  `surveyUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Stores UID for Feedback/Survey',
  `noOfQuestion` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '1',
  `sessionConfig` longtext COLLATE utf8mb4_general_ci COMMENT 'JSON: Stores timings, geofencing & check-in rules for Attendance, Pre, Post & Survey',
  `checklistUid` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Comma-separated SubCategory IDs',
  `purchaseTariff` decimal(10,2) NOT NULL DEFAULT '0.00',
  `purchaseTax` varchar(10) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Nett',
  `totalTax` decimal(10,2) NOT NULL DEFAULT '0.00',
  `totalPurchase` decimal(10,2) NOT NULL DEFAULT '0.00',
  `totalWithTax` decimal(10,2) NOT NULL DEFAULT '0.00',
  `commissionFromPartner` decimal(10,2) NOT NULL DEFAULT '0.00',
  `TDSRate` varchar(10) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Nett',
  `TDS` decimal(10,2) NOT NULL DEFAULT '0.00',
  `finalBillValue` decimal(10,2) NOT NULL DEFAULT '0.00',
  `salesTariff` decimal(10,2) NOT NULL DEFAULT '0.00',
  `salesTax` varchar(10) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Nett',
  `totalSalesTax` decimal(10,2) NOT NULL DEFAULT '0.00',
  `totalSales` decimal(10,2) NOT NULL DEFAULT '0.00',
  `totalSalesWithTax` decimal(10,2) NOT NULL DEFAULT '0.00',
  `discounts` decimal(10,2) NOT NULL DEFAULT '0.00',
  `finalSaleValue` decimal(10,2) NOT NULL DEFAULT '0.00',
  `attendanceSheet` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hotelBill` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `conferenceImage` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `startConferenceImage` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hotelInvoiceFile` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `travelInvoiceFile` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `saleInvoiceFile` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `paymentReceiptFile` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tdsCertificateFile` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `auditStatus` varchar(50) COLLATE utf8mb4_general_ci DEFAULT 'Pending',
  `auditRemarks` longtext COLLATE utf8mb4_general_ci,
  `auditBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `auditDate` timestamp NULL DEFAULT NULL,
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `data_scopes`
--

CREATE TABLE `data_scopes` (
  `id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `table_type` enum('admin','agencyteam','trainee') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `scope_type` enum('zone','state','region','district','trainer_id') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `scope_value` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `faq`
--

CREATE TABLE `faq` (
  `id` int NOT NULL,
  `faqUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `question` mediumtext COLLATE utf8mb4_general_ci,
  `answer` longtext COLLATE utf8mb4_general_ci,
  `visibleOnWeb` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `heroimage`
--

CREATE TABLE `heroimage` (
  `id` int NOT NULL,
  `heroUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `heroImage` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `category` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategory` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `shortTitle` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `referralLink` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `activeStatus` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `approvedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `logsmaster`
--

CREATE TABLE `logsmaster` (
  `id` int NOT NULL,
  `logsUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `securedPassword` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `role` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `login_IP` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `loginTime` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logoutTime` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `newsletter`
--

CREATE TABLE `newsletter` (
  `id` int NOT NULL,
  `newsletterUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `updatedBy` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `isread` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `remarks` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `pincode`
--

CREATE TABLE `pincode` (
  `id` int NOT NULL,
  `pincodeUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `circleName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `regionName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `divisionName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `officeName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pincode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `officeType` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `delivery` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `district` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `stateName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `latitude` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `longitude` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `portfolio`
--

CREATE TABLE `portfolio` (
  `id` int NOT NULL,
  `portfolioUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `title` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `summary` longtext COLLATE utf8mb4_general_ci,
  `tags` mediumtext COLLATE utf8mb4_general_ci,
  `description` longtext COLLATE utf8mb4_general_ci,
  `image` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `thumbnails` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `video` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `onTranding` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `trandingTill` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '00/00/00',
  `latest` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `newsFlash` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `featuredStories` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `isRead` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `query`
--

CREATE TABLE `query` (
  `id` int NOT NULL,
  `queryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `subject` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `message` mediumtext COLLATE utf8mb4_general_ci,
  `updatedBy` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `remarks` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `isRead` varchar(100) COLLATE utf8mb4_general_ci DEFAULT 'No',
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` mediumtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `questions`
--

CREATE TABLE `questions` (
  `id` int NOT NULL,
  `assessmentSuiteUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `question` longtext COLLATE utf8mb4_general_ci,
  `question_type` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'multiple_choice',
  `sort_order` int DEFAULT '0',
  `options` longtext COLLATE utf8mb4_general_ci,
  `correct_answer` longtext COLLATE utf8mb4_general_ci,
  `points` int DEFAULT '0',
  `settings` longtext COLLATE utf8mb4_general_ci COMMENT 'Stores JSON for timer, required toggle, etc',
  `descriptions` longtext COLLATE utf8mb4_general_ci,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Approved',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `salarysheet`
--

CREATE TABLE `salarysheet` (
  `id` int NOT NULL,
  `salarySheetUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `band` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `salary` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `convenceFee` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `targetAmount` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `netGST` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `netAssociate` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `services`
--

CREATE TABLE `services` (
  `id` int NOT NULL,
  `servicesUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `title` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `summary` longtext COLLATE utf8mb4_general_ci,
  `tags` mediumtext COLLATE utf8mb4_general_ci,
  `description` longtext COLLATE utf8mb4_general_ci,
  `image` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `thumbnails` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `video` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `onTranding` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `trandingTill` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '00/00/00',
  `latest` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `newsFlash` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `featuredStories` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `isRead` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `subcategory`
--

CREATE TABLE `subcategory` (
  `id` int NOT NULL,
  `subCategoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `categoryUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `subCategory` varchar(200) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `description` longtext COLLATE utf8mb4_general_ci,
  `visibleOnWeb` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `token` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `system_modules`
--

CREATE TABLE `system_modules` (
  `id` int NOT NULL,
  `module_key` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `module_name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `trainee`
--

CREATE TABLE `trainee` (
  `id` int NOT NULL,
  `traineeUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zone` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `region` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `company` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `requestedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerEmployeeId` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `trainerName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `supervisorUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `supervisorName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `supervisorDesignation` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `uid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `agencyId` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `designation` varchar(150) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `gender` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `district` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `profilePhoto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT 'default.png',
  `address` text COLLATE utf8mb4_general_ci,
  `altPhone` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `altEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `joinedOn` date DEFAULT NULL,
  `jobCity` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobState` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `jobPincode` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `resignedOn` date DEFAULT NULL,
  `jobStatus` varchar(50) COLLATE utf8mb4_general_ci DEFAULT 'Active',
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(100) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `remarks` longtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user_permissions`
--

CREATE TABLE `user_permissions` (
  `id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `table_type` enum('admin','agencyteam','trainee') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `module_id` int DEFAULT NULL,
  `can_read` tinyint(1) DEFAULT '0',
  `can_write` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `venue`
--

CREATE TABLE `venue` (
  `id` int NOT NULL,
  `venueUid` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zone` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `region` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `company` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `phone` bigint DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `district` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `state` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pincode` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `map` longtext COLLATE utf8mb4_general_ci,
  `contactPersonName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `contactPersonPhone` bigint DEFAULT NULL,
  `venueType` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tariff` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tax` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `commission` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bankName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ifsc` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bankAccountNo` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bankHolderName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `upi` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hotelQR` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `registeredName` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `GSTNumber` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `GSTPhone` bigint DEFAULT NULL,
  `GSTEmail` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `GSTAddress` longtext COLLATE utf8mb4_general_ci,
  `image1` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `image2` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `image3` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `image4` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `image5` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `image6` varchar(250) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `brochure` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `gstCertificate` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `addressProof` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `MSMECertificate` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `fssaiCertificate` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `additionalDocs` varchar(300) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `filePath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logPath` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `excelUploadedOn` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updatedBy` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updationOn` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `isRead` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'No',
  `token` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `contractExpired` date DEFAULT NULL,
  `remarks` mediumtext COLLATE utf8mb4_general_ci,
  `securityDetails` longtext COLLATE utf8mb4_general_ci,
  `masterRemarks` longtext COLLATE utf8mb4_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `accountsUid` (`accountsUid`);

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `adminUid` (`adminUid`);

--
-- Indexes for table `advertising`
--
ALTER TABLE `advertising`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `advertisingUid` (`advertisingUid`);

--
-- Indexes for table `agency`
--
ALTER TABLE `agency`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `agencyUid` (`agencyUid`),
  ADD UNIQUE KEY `email` (`email`,`phone`,`certificateNo`);

--
-- Indexes for table `agencyteam`
--
ALTER TABLE `agencyteam`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uid` (`agencyTeamUid`),
  ADD UNIQUE KEY `email` (`email`,`phone`,`officialEmail`,`offerId`),
  ADD KEY `idx_supervisor_lookup` (`companyUid`,`role`,`status`);

--
-- Indexes for table `assessment`
--
ALTER TABLE `assessment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_live_quiz_fast_lookup` (`conferenceUid`,`assessmentSuiteUid`,`traineeUid`);

--
-- Indexes for table `assessmentsuite`
--
ALTER TABLE `assessmentsuite`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `assessmentSuiteUid` (`assessmentSuiteUid`);

--
-- Indexes for table `assessment_results`
--
ALTER TABLE `assessment_results`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_attempt` (`traineeUid`,`assessmentSuiteUid`,`attemptNumber`),
  ADD KEY `idx_conf_suite` (`conferenceUid`,`assessmentSuiteUid`);

--
-- Indexes for table `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `attendanceUid` (`attendanceUid`),
  ADD UNIQUE KEY `unique_session_attendance` (`conferenceUid`,`traineeUid`),
  ADD KEY `idx_conf_uid` (`conferenceUid`),
  ADD KEY `idx_trainee_uid` (`traineeUid`);

--
-- Indexes for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_checkin` (`conferenceUid`,`traineeUid`,`moduleId`),
  ADD KEY `idx_lookup` (`conferenceUid`,`traineeUid`);

--
-- Indexes for table `blogs`
--
ALTER TABLE `blogs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `booking`
--
ALTER TABLE `booking`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uid` (`bookingUid`);

--
-- Indexes for table `career`
--
ALTER TABLE `career`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `adminUid` (`careerUid`);

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `companydetails`
--
ALTER TABLE `companydetails`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `companyId` (`companyUid`);

--
-- Indexes for table `conference`
--
ALTER TABLE `conference`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `conferenceUid` (`conferenceUid`);

--
-- Indexes for table `data_scopes`
--
ALTER TABLE `data_scopes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_lookup` (`user_id`,`table_type`);

--
-- Indexes for table `faq`
--
ALTER TABLE `faq`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uid` (`faqUid`);

--
-- Indexes for table `heroimage`
--
ALTER TABLE `heroimage`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `heroUid` (`heroUid`);

--
-- Indexes for table `logsmaster`
--
ALTER TABLE `logsmaster`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `logUid` (`logsUid`);

--
-- Indexes for table `newsletter`
--
ALTER TABLE `newsletter`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `pincode`
--
ALTER TABLE `pincode`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `pincodeUid` (`pincodeUid`);

--
-- Indexes for table `portfolio`
--
ALTER TABLE `portfolio`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `query`
--
ALTER TABLE `query`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `salarysheet`
--
ALTER TABLE `salarysheet`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `salarySheetUid` (`salarySheetUid`);

--
-- Indexes for table `services`
--
ALTER TABLE `services`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `subcategory`
--
ALTER TABLE `subcategory`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `system_modules`
--
ALTER TABLE `system_modules`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `module_key` (`module_key`);

--
-- Indexes for table `trainee`
--
ALTER TABLE `trainee`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `traineeUID` (`traineeUid`),
  ADD UNIQUE KEY `phone` (`phone`),
  ADD UNIQUE KEY `uid` (`uid`,`email`),
  ADD UNIQUE KEY `username_unique` (`username`),
  ADD KEY `idx_supervisorUid` (`supervisorUid`),
  ADD KEY `idx_trainee_status` (`status`);

--
-- Indexes for table `user_permissions`
--
ALTER TABLE `user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_module_unique` (`user_id`,`table_type`,`module_id`),
  ADD KEY `module_id` (`module_id`);

--
-- Indexes for table `venue`
--
ALTER TABLE `venue`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `venueUid` (`venueUid`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `accounts`
--
ALTER TABLE `accounts`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `advertising`
--
ALTER TABLE `advertising`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `agency`
--
ALTER TABLE `agency`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `agencyteam`
--
ALTER TABLE `agencyteam`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `assessment`
--
ALTER TABLE `assessment`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `assessmentsuite`
--
ALTER TABLE `assessmentsuite`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `assessment_results`
--
ALTER TABLE `assessment_results`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `blogs`
--
ALTER TABLE `blogs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `booking`
--
ALTER TABLE `booking`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `career`
--
ALTER TABLE `career`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `category`
--
ALTER TABLE `category`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `companydetails`
--
ALTER TABLE `companydetails`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `conference`
--
ALTER TABLE `conference`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `data_scopes`
--
ALTER TABLE `data_scopes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `faq`
--
ALTER TABLE `faq`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `heroimage`
--
ALTER TABLE `heroimage`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `logsmaster`
--
ALTER TABLE `logsmaster`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `newsletter`
--
ALTER TABLE `newsletter`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `pincode`
--
ALTER TABLE `pincode`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `portfolio`
--
ALTER TABLE `portfolio`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `query`
--
ALTER TABLE `query`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `salarysheet`
--
ALTER TABLE `salarysheet`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `services`
--
ALTER TABLE `services`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `subcategory`
--
ALTER TABLE `subcategory`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `system_modules`
--
ALTER TABLE `system_modules`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `trainee`
--
ALTER TABLE `trainee`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_permissions`
--
ALTER TABLE `user_permissions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `venue`
--
ALTER TABLE `venue`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `user_permissions`
--
ALTER TABLE `user_permissions`
  ADD CONSTRAINT `fk_up_module` FOREIGN KEY (`module_id`) REFERENCES `system_modules` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
