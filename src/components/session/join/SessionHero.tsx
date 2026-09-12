import { Image, ImageSourcePropType, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";

type SessionHeroProps = {
  avatar: ImageSourcePropType;
  name: string;
  phone: string;
};

export default function SessionHero({ avatar, name, phone }: SessionHeroProps) {
  return (
    <View style={styles.hero}>
      <Image source={avatar} style={styles.avatar} />
      <AppText style={styles.name}>{name}</AppText>
      <AppText style={styles.phone}>{phone}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    height: "45%",
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    paddingTop: "20%",
    borderTopLeftRadius: Fonts.br,
    borderTopRightRadius: Fonts.br,
  },
  avatar: {
    width: 150,
    height: 131,
    marginBottom: 2,
  },
  name: { fontSize: 26, color: "white", marginBottom: 4 },
  phone: {
    fontSize: 15,
    color: Colors.white,
    backgroundColor: "#398CFF",
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 4,
    marginTop: 3,
  },
});
