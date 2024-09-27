public class num2str {

    public String[] convertArrayToString(Object[] elements) {
        String[] result = new String[elements.length];
        String invisibleChar = "\u200B";  // Zero-width space

        for (int i = 0; i < elements.length; i++) {
            if (elements[i] instanceof Number) {
                Number num = (Number) elements[i];
                // Check if the number is an integer (not a floating point with a decimal part)
                if (num instanceof Integer || (num.doubleValue() == Math.floor(num.doubleValue()) && !Double.isInfinite(num.doubleValue()))) {
                    // If it's an integer, convert to string without '.0'
                    result[i] = invisibleChar + String.valueOf(num.intValue());
                } else {
                    // If it's a floating-point number, convert as usual
                    result[i] = invisibleChar + String.valueOf(num.doubleValue());
                }
            } else if (elements[i] != null) {
                // Handle non-numeric values by converting them to strings
                result[i] = elements[i].toString();
            } else {
                // Handle null values by returning an empty string
                result[i] = "";
            }
        }

        return result;
    }
}

