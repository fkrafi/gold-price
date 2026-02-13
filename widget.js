function delta(value) {
    let color;
    let arrow;

    if (value < 0) {
        color = 'red';
        arrow = '↓';
    } else {
        color = 'green';
        arrow = '↑';
    }

    return {
        formattedValue: `${arrow} ${Math.abs(value)}`,
        cssClass: color
    };
}