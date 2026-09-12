import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

type PaginationProps = {
  page: number;
  pageCount: number;
  totalRows: number;
  rangeStart: number;
  rangeEnd: number;
  onPageChange: (page: number) => void;
};

// Always just the first and last page number, never anything in between.
function buildPageList(pageCount: number): (number | "ellipsis")[] {
  if (pageCount <= 1) return [1];
  if (pageCount === 2) return [1, 2];
  return [1, "ellipsis", pageCount];
}

export default function Pagination({ page, pageCount, totalRows, rangeStart, rangeEnd, onPageChange }: PaginationProps) {
  const pages = buildPageList(pageCount);

  return (
    <View style={styles.container}>
      <View style={styles.summaryBox}>
        <AppText style={styles.summary} color={Colors.gray600}>
          {totalRows === 0
            ? "Showing 0 entries"
            : `Showing ${rangeStart} to ${rangeEnd} of ${totalRows} entries`}
        </AppText>
      </View>

      <View style={styles.controlsBox}>
        <View style={styles.controls}>
          <PageButton disabled={page <= 1} onPress={() => onPageChange(1)}>
            <Ionicons name="play-back" size={13} color={page <= 1 ? Colors.gray400 : Colors.mainColour1} />
          </PageButton>
          <PageButton disabled={page <= 1} onPress={() => onPageChange(page - 1)}>
            <Ionicons name="chevron-back" size={15} color={page <= 1 ? Colors.gray400 : Colors.mainColour1} />
          </PageButton>

          {pages.map((entry, index) =>
            entry === "ellipsis" ? (
              <AppText key={`ellipsis-${index}`} style={styles.ellipsis} color={Colors.gray400}>
                ...
              </AppText>
            ) : (
              <PageButton key={entry} active={entry === page} onPress={() => onPageChange(entry)}>
                <AppText
                  style={styles.pageNumber}
                  color={entry === page ? Colors.white : Colors.gray600}
                  weight={entry === page ? FontWeight.semiBold : FontWeight.medium}
                >
                  {entry}
                </AppText>
              </PageButton>
            )
          )}

          <PageButton disabled={page >= pageCount} onPress={() => onPageChange(page + 1)}>
            <Ionicons name="chevron-forward" size={15} color={page >= pageCount ? Colors.gray400 : Colors.mainColour1} />
          </PageButton>
          <PageButton disabled={page >= pageCount} onPress={() => onPageChange(pageCount)}>
            <Ionicons name="play-forward" size={13} color={page >= pageCount ? Colors.gray400 : Colors.mainColour1} />
          </PageButton>
        </View>
      </View>
    </View>
  );
}

function PageButton({
  children,
  onPress,
  disabled,
  active,
}: {
  children: React.ReactNode;
  onPress: () => void;
  disabled?: boolean;
  active?: boolean;
}) {
  return (
    <Pressable
      style={[styles.pageButton, active && styles.pageButtonActive]}
      onPress={onPress}
      disabled={disabled}
      hitSlop={4}
    >
      {children}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    flexWrap: "wrap",
  },
  summaryBox: {
    flex: 1,
    minWidth: 35,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
    paddingHorizontal: 6,
    paddingVertical: 8,
  },
  summary: { fontSize: Fonts.overline },
  controlsBox: {
    flex: 1,
    minWidth: 140,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
    paddingHorizontal: 4,
    paddingVertical: 6,
  },
  controls: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4, flexWrap: "wrap" },
  pageButton: {
    minWidth: 26,
    height: 26,
    borderRadius: Radius.md,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
    backgroundColor: Colors.gray100,
  },
  pageButtonActive: { backgroundColor: Colors.mainColour1 },
  pageNumber: { fontSize: Fonts.overline },
  ellipsis: { fontSize: Fonts.overline, marginHorizontal: 2 },
});
