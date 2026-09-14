import React, {
    forwardRef,
    useMemo,
} from "react";

import BottomSheet from "@gorhom/bottom-sheet";

import { View } from "react-native";

const RegisterBottomSheet = forwardRef<React.ComponentRef<typeof BottomSheet>>((
    _props,
    ref,
) => {
    const snapPoints = useMemo(() => ["90%"], []);
    return (
        <BottomSheet
            ref={ref}
            index={-1}
            snapPoints={snapPoints}
            enablePanDownToClose
        >
            <View>
            </View>
        </BottomSheet>

    );

});

RegisterBottomSheet.displayName = "RegisterBottomSheet";

export default RegisterBottomSheet;
