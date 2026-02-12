from unittest.mock import patch, MagicMock
from capture import capture_area


def test_capture_area_calls_overlay_and_screenshots():
    # Mock overlay to return a 100x80 region (10,20)->(110,100)
    with patch('area_overlay.select_region') as mock_sel:
        mock_sel.return_value = (10, 20, 110, 100)
        # Mock internal MSS region capture to return a fake image object
        fake_img = MagicMock()
        fake_img.size = (100, 80)
        with patch('capture._mss_shot_region') as mock_mss:
            mock_mss.return_value = fake_img
            img = capture_area()
            assert img is not None
            # ensure mss region shot was called and returned our fake image
            assert mock_mss.called
            assert img is fake_img
