// All 28 Indian states + 8 union territories, alphabetical, each with its
// major cities/districts for the District picker that's gated on this.
export const STATES = [
  {
    label: "Andaman and Nicobar Islands",
    value: "andaman_and_nicobar_islands",
    cities: [{ label: "Port Blair", value: "port_blair" }],
  },
  {
    label: "Andhra Pradesh",
    value: "andhra_pradesh",
    cities: [
      { label: "Visakhapatnam", value: "visakhapatnam" },
      { label: "Vijayawada", value: "vijayawada" },
      { label: "Guntur", value: "guntur" },
      { label: "Tirupati", value: "tirupati" },
    ],
  },
  {
    label: "Arunachal Pradesh",
    value: "arunachal_pradesh",
    cities: [
      { label: "Itanagar", value: "itanagar" },
      { label: "Naharlagun", value: "naharlagun" },
      { label: "Tawang", value: "tawang" },
    ],
  },
  {
    label: "Assam",
    value: "assam",
    cities: [
      { label: "Guwahati", value: "guwahati" },
      { label: "Dibrugarh", value: "dibrugarh" },
      { label: "Silchar", value: "silchar" },
      { label: "Jorhat", value: "jorhat" },
    ],
  },
  {
    label: "Bihar",
    value: "bihar",
    cities: [
      { label: "Patna", value: "patna" },
      { label: "Gaya", value: "gaya" },
      { label: "Bhagalpur", value: "bhagalpur" },
      { label: "Muzaffarpur", value: "muzaffarpur" },
    ],
  },
  {
    label: "Chandigarh",
    value: "chandigarh",
    cities: [{ label: "Chandigarh", value: "chandigarh_city" }],
  },
  {
    label: "Chhattisgarh",
    value: "chhattisgarh",
    cities: [
      { label: "Raipur", value: "raipur" },
      { label: "Bhilai", value: "bhilai" },
      { label: "Bilaspur", value: "bilaspur" },
      { label: "Durg", value: "durg" },
    ],
  },
  {
    label: "Dadra and Nagar Haveli and Daman and Diu",
    value: "dadra_nh_daman_diu",
    cities: [
      { label: "Daman", value: "daman" },
      { label: "Silvassa", value: "silvassa" },
    ],
  },
  {
    label: "Delhi",
    value: "delhi",
    cities: [
      { label: "New Delhi", value: "new_delhi" },
      { label: "Rohini", value: "rohini" },
      { label: "Dwarka", value: "dwarka" },
      { label: "Karol Bagh", value: "karol_bagh" },
    ],
  },
  {
    label: "Goa",
    value: "goa",
    cities: [
      { label: "Panaji", value: "panaji" },
      { label: "Margao", value: "margao" },
      { label: "Vasco da Gama", value: "vasco_da_gama" },
    ],
  },
  {
    label: "Gujarat",
    value: "gujarat",
    cities: [
      { label: "Ahmedabad", value: "ahmedabad" },
      { label: "Surat", value: "surat" },
      { label: "Vadodara", value: "vadodara" },
      { label: "Rajkot", value: "rajkot" },
    ],
  },
  {
    label: "Haryana",
    value: "haryana",
    cities: [
      { label: "Gurugram", value: "gurugram" },
      { label: "Faridabad", value: "faridabad" },
      { label: "Panipat", value: "panipat" },
      { label: "Karnal", value: "karnal" },
    ],
  },
  {
    label: "Himachal Pradesh",
    value: "himachal_pradesh",
    cities: [
      { label: "Shimla", value: "shimla" },
      { label: "Manali", value: "manali" },
      { label: "Dharamshala", value: "dharamshala" },
    ],
  },
  {
    label: "Jammu and Kashmir",
    value: "jammu_and_kashmir",
    cities: [
      { label: "Srinagar", value: "srinagar" },
      { label: "Jammu", value: "jammu" },
    ],
  },
  {
    label: "Jharkhand",
    value: "jharkhand",
    cities: [
      { label: "Ranchi", value: "ranchi" },
      { label: "Jamshedpur", value: "jamshedpur" },
      { label: "Dhanbad", value: "dhanbad" },
      { label: "Bokaro", value: "bokaro" },
    ],
  },
  {
    label: "Karnataka",
    value: "karnataka",
    cities: [
      { label: "Bengaluru", value: "bengaluru" },
      { label: "Mysuru", value: "mysuru" },
      { label: "Mangaluru", value: "mangaluru" },
      { label: "Hubballi", value: "hubballi" },
    ],
  },
  {
    label: "Kerala",
    value: "kerala",
    cities: [
      { label: "Kochi", value: "kochi" },
      { label: "Thiruvananthapuram", value: "thiruvananthapuram" },
      { label: "Kozhikode", value: "kozhikode" },
      { label: "Kollam", value: "kollam" },
    ],
  },
  {
    label: "Ladakh",
    value: "ladakh",
    cities: [
      { label: "Leh", value: "leh" },
      { label: "Kargil", value: "kargil" },
    ],
  },
  {
    label: "Lakshadweep",
    value: "lakshadweep",
    cities: [{ label: "Kavaratti", value: "kavaratti" }],
  },
  {
    label: "Madhya Pradesh",
    value: "madhya_pradesh",
    cities: [
      { label: "Bhopal", value: "bhopal" },
      { label: "Indore", value: "indore" },
      { label: "Gwalior", value: "gwalior" },
      { label: "Jabalpur", value: "jabalpur" },
    ],
  },
  {
    label: "Maharashtra",
    value: "maharashtra",
    cities: [
      { label: "Mumbai", value: "mumbai" },
      { label: "Pune", value: "pune" },
      { label: "Nagpur", value: "nagpur" },
      { label: "Nashik", value: "nashik" },
    ],
  },
  {
    label: "Manipur",
    value: "manipur",
    cities: [{ label: "Imphal", value: "imphal" }],
  },
  {
    label: "Meghalaya",
    value: "meghalaya",
    cities: [{ label: "Shillong", value: "shillong" }],
  },
  {
    label: "Mizoram",
    value: "mizoram",
    cities: [{ label: "Aizawl", value: "aizawl" }],
  },
  {
    label: "Nagaland",
    value: "nagaland",
    cities: [
      { label: "Kohima", value: "kohima" },
      { label: "Dimapur", value: "dimapur" },
    ],
  },
  {
    label: "Odisha",
    value: "odisha",
    cities: [
      { label: "Bhubaneswar", value: "bhubaneswar" },
      { label: "Cuttack", value: "cuttack" },
      { label: "Rourkela", value: "rourkela" },
    ],
  },
  {
    label: "Puducherry",
    value: "puducherry",
    cities: [
      { label: "Puducherry", value: "puducherry_city" },
      { label: "Karaikal", value: "karaikal" },
    ],
  },
  {
    label: "Punjab",
    value: "punjab",
    cities: [
      { label: "Ludhiana", value: "ludhiana" },
      { label: "Amritsar", value: "amritsar" },
      { label: "Jalandhar", value: "jalandhar" },
      { label: "Patiala", value: "patiala" },
    ],
  },
  {
    label: "Rajasthan",
    value: "rajasthan",
    cities: [
      { label: "Jaipur", value: "jaipur" },
      { label: "Jodhpur", value: "jodhpur" },
      { label: "Udaipur", value: "udaipur" },
      { label: "Kota", value: "kota" },
    ],
  },
  {
    label: "Sikkim",
    value: "sikkim",
    cities: [{ label: "Gangtok", value: "gangtok" }],
  },
  {
    label: "Tamil Nadu",
    value: "tamil_nadu",
    cities: [
      { label: "Chennai", value: "chennai" },
      { label: "Coimbatore", value: "coimbatore" },
      { label: "Madurai", value: "madurai" },
      { label: "Tiruchirappalli", value: "tiruchirappalli" },
    ],
  },
  {
    label: "Telangana",
    value: "telangana",
    cities: [
      { label: "Hyderabad", value: "hyderabad" },
      { label: "Warangal", value: "warangal" },
      { label: "Nizamabad", value: "nizamabad" },
    ],
  },
  {
    label: "Tripura",
    value: "tripura",
    cities: [{ label: "Agartala", value: "agartala" }],
  },
  {
    label: "Uttar Pradesh",
    value: "up",
    cities: [
      { label: "Noida", value: "noida" },
      { label: "Greater Noida", value: "greater_noida" },
      { label: "Lucknow", value: "lucknow" },
      { label: "Kanpur", value: "kanpur" },
      { label: "Varanasi", value: "varanasi" },
      { label: "Agra", value: "agra" },
    ],
  },
  {
    label: "Uttarakhand",
    value: "uttarakhand",
    cities: [
      { label: "Dehradun", value: "dehradun" },
      { label: "Haridwar", value: "haridwar" },
      { label: "Nainital", value: "nainital" },
    ],
  },
  {
    label: "West Bengal",
    value: "west_bengal",
    cities: [
      { label: "Kolkata", value: "kolkata" },
      { label: "Howrah", value: "howrah" },
      { label: "Durgapur", value: "durgapur" },
      { label: "Siliguri", value: "siliguri" },
    ],
  },
];
