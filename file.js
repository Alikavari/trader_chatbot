function getTimezoneBias() {
    const offsetMinutes = new Date().getTimezoneOffset(); // minutes behind UTC
    const totalMinutes = -offsetMinutes; // invert because JS returns negative for ahead of UTC
    const sign = totalMinutes >= 0 ? "+" : "-";
    const absMinutes = Math.abs(totalMinutes);
    const hours = Math.floor(absMinutes / 60);
    const minutes = absMinutes % 60;
    return sign + hours.toString().padStart(2, '0') + ":" + minutes.toString().padStart(2, '0');
}

// Example usage
console.log(getTimezoneBias()); // e.g., "+03:30"
